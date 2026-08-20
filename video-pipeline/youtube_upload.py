import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import google.auth.transport.requests
import logging
import json
import time # 딜레이를 위해 추가
from datetime import datetime, timedelta, timezone

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OAuth 2.0 인증 범위 설정
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

def get_authenticated_service(credentials_file=None):
    """YouTube API 서비스에 대한 인증된 객체를 반환합니다."""
    credentials = None

    if credentials_file and os.path.exists(credentials_file):
        try:
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(credentials_file, SCOPES)
            logging.info(f"✅ 저장된 YouTube API 자격 증명 로드 완료: {credentials_file}")
        except Exception as e:
            logging.warning(f"⚠️ 저장된 YouTube API 자격 증명 로드 실패: {e}")
            credentials = None
    else:
        logging.error(f"❌ 자격 증명 파일 '{credentials_file}'을 찾을 수 없습니다.")
        raise Exception("YouTube API 인증 실패")

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(google.auth.transport.requests.Request())
                with open(credentials_file, 'w') as token:
                    token.write(credentials.to_json())
                logging.info("✅ 자격 증명 새로고침 및 저장 완료.")
            except Exception as e:
                logging.error(f"❌ 자격 증명 새로고침 실패: {e}")
                raise
        else:
            raise Exception("YouTube API 인증 실패: 자격 증명 무효")

    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def get_or_create_playlist(youtube, title):
    """해당 제목의 재생목록 ID를 반환. 없으면 새로 생성."""
    playlists = youtube.playlists().list(part="snippet", mine=True, maxResults=50).execute()
    for item in playlists.get("items", []):
        if item["snippet"]["title"] == title:
            return item["id"]

    # 없으면 새로 생성
    logging.info(f"➕ 재생목록 '{title}' 생성 중...")
    new_playlist = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": f"{title}에 자동 업로드됨"},
            "status": {"privacyStatus": "public"}
        }
    ).execute()
    logging.info(f"✅ 재생목록 '{title}' 생성 완료. ID: {new_playlist['id']}")
    return new_playlist["id"]

def add_video_to_playlist(youtube, video_id, playlist_id):
    """비디오를 재생목록에 추가"""
    try:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id}
                }
            }
        ).execute()
        logging.info(f"📁 비디오 '{video_id}'가 재생목록 '{playlist_id}'에 추가 완료.")
    except googleapiclient.errors.HttpError as e:
        if e.resp.status == 409:
            logging.warning(f"⚠️ 비디오 '{video_id}'는 이미 재생목록 '{playlist_id}'에 존재합니다. (HttpError 409)")
        else:
            logging.error(f"❌ 재생목록에 비디오 추가 중 오류 발생 (HttpError): {e.resp.status} - {e.content}")
            raise
    except Exception as e:
        logging.error(f"❌ 재생목록에 비디오 추가 중 예기치 않은 오류: {e}")
        raise

def insert_comment(youtube, video_id, text):
    """
    비디오에 댓글을 등록하고 댓글 ID를 반환합니다.
    """
    try:
        response = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": text
                        }
                    }
                }
            }
        ).execute()
        
        # 생성된 최상위 댓글의 ID 추출
        comment_id = response['snippet']['topLevelComment']['id']
        logging.info(f"💬 비디오 '{video_id}'에 댓글 등록 완료. Comment ID: {comment_id}")
        return comment_id

    except googleapiclient.errors.HttpError as e:
        logging.error(f"❌ 댓글 등록 실패 (API 오류): {e.resp.status} - {e.content}")
        return None
    except Exception as e:
        logging.error(f"❌ 댓글 등록 실패 (예기치 않은 오류): {e}")
        return None

def rate_comment(youtube, comment_id, rating='like'):
    """
    댓글에 좋아요(like), 싫어요(dislike), 또는 없음(none)을 설정합니다.
    참고: YouTube Data API v3는 '작성자 하트(Creator Heart)' 기능을 공식 지원하지 않습니다.
    """
    try:
        # [FIXED] 'rate' 메서드 대신 올바른 'setRating' 메서드 사용
        youtube.comments().setRating(
            id=comment_id,
            rating=rating
        ).execute()
        logging.info(f"👍 댓글 '{comment_id}'에 '{rating}' 처리 완료.")
    except googleapiclient.errors.HttpError as e:
        logging.error(f"❌ 댓글 좋아요 실패 (API 오류): {e.resp.status} - {e.content}")
    except Exception as e:
        logging.error(f"❌ 댓글 좋아요 실패 (예기치 않은 오류): {e}")

def get_next_available_schedule_time_kst():
    """KST 기준으로 다음 예약 업로드 시간 계산"""
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    logging.info(f"현재 KST 시간: {now_kst}")

    min_publish_time = now_kst + timedelta(minutes=31)
    min_publish_time = min_publish_time.replace(second=0, microsecond=0)

    minute = min_publish_time.minute
    
    if minute == 0:
        scheduled_time = min_publish_time
    elif 0 < minute <= 30:
        scheduled_time = min_publish_time.replace(minute=30)
    else:
        scheduled_time = min_publish_time.replace(minute=0) + timedelta(hours=1)
    
    while scheduled_time <= now_kst + timedelta(minutes=30):
        scheduled_time += timedelta(minutes=30)
        scheduled_time = scheduled_time.replace(second=0, microsecond=0)
        if scheduled_time.minute >= 60:
            scheduled_time = scheduled_time.replace(minute=scheduled_time.minute - 60) + timedelta(hours=1)

    logging.info(f"YouTube 예약 업로드 시간 (KST): {scheduled_time}")
    return scheduled_time.isoformat(timespec='seconds')

def upload_video(file_path, title, description, tags, privacy_status, credentials_file, playlists_to_add=None, thumbnail_path=None, scheduled_publish_at=None, comment_text=None, related_video_id=None, category_id="27"):
    """
    YouTube에 비디오를 업로드합니다.
    - scheduled_publish_at과 comment_text가 모두 있는 경우:
      '일부공개(unlisted)' 업로드 -> 대기(10초) -> 댓글 작성 -> 좋아요 -> 대기(2초) -> '비공개(private)' 및 예약 설정으로 전환
    - related_video_id: 관련 동영상(Shorts remix source 등) ID를 받지만, API v3 미지원으로 인해 로깅만 수행.
    - category_id: YouTube 카테고리 ID (기본값 "27" 교육. 미전달 시 기존 동작 유지)
      주요 카테고리: "25" 뉴스/정치, "27" 교육, "22" 사람/블로그, "28" 과학/기술
    """
    if playlists_to_add is None:
        playlists_to_add = []

    # [MODIFIED] 제목 유효성 강제 검사 (Error 2 해결)
    if not title or not title.strip():
        logging.warning("⚠️ Invalid title detected. Using default title.")
        title = f"Crypto News Update {datetime.now().strftime('%Y-%m-%d')}"
    
    # 꺽쇠 괄호 제거 (유튜브 API 오류 방지)
    title = title.replace('<', '').replace('>', '')

    try:
        youtube_service = get_authenticated_service(credentials_file=credentials_file)

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id  # 호출측에서 지정 가능. 기본값 "27"(교육)
            },
            "status": {
                "privacyStatus": privacy_status,
                "madeForKids": False
            },
            "contentDetails": {
                "syntheticMedia": {
                    "syntheticMediaType": "NONE"
                }
            }
        }

        # 관련 동영상 ID 처리 (API 미지원이므로 로그만 출력)
        if related_video_id:
            logging.info(f"ℹ️ 관련 동영상 ID({related_video_id})가 전달되었습니다. (참고: YouTube API v3는 현재 Shorts 관련 동영상 속성 설정을 자동화할 수 없으므로, 설명란 링크 등을 확인해주세요.)")

        # --- 예약 업로드 + 댓글 작성 전략 ---
        perform_schedule_update_later = False
        
        if scheduled_publish_at and comment_text:
            logging.info("💡 예약 업로드 및 댓글 작성을 위해 '일부 공개(unlisted)'로 먼저 업로드합니다.")
            body["status"]["privacyStatus"] = "unlisted"
            perform_schedule_update_later = True
        elif scheduled_publish_at:
            body["status"]["publishAt"] = scheduled_publish_at
            logging.info(f"📅 비디오 예약 시간 설정: {scheduled_publish_at}")
            if body["status"]["privacyStatus"] != 'private':
                logging.warning("⚠️ 예약 게시를 위해 privacyStatus를 'private'으로 강제 변경합니다.")
                body["status"]["privacyStatus"] = 'private'

        logging.debug(f"📤 YouTube API videos.insert 요청 body: {json.dumps(body, indent=2)}")

        media_body = googleapiclient.http.MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = youtube_service.videos().insert(
            part="snippet,status,contentDetails",
            body=body,
            media_body=media_body
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f"⬆️ 업로드 진행률: {int(status.progress() * 100)}%")

        video_id = response.get('id')
        logging.info(f"✅ 업로드 성공! 비디오 ID: {video_id}")

        # --- [안전 장치 1] 비디오 처리 대기 (10초) ---
        # 비디오가 업로드된 직후에는 유튜브 내부 처리가 덜 되어 댓글 기능이 활성화되지 않았을 수 있습니다.
        if comment_text:
            wait_time = 10
            logging.info(f"⏳ 비디오 처리 및 댓글 시스템 동기화를 위해 {wait_time}초 대기합니다...")
            time.sleep(wait_time)

        # 1. 썸네일 업로드
        if thumbnail_path and os.path.exists(thumbnail_path):
            logging.info(f"🖼️ 썸네일 파일 '{thumbnail_path}' 업로드 시도 중...")
            try:
                thumbnail_media = googleapiclient.http.MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
                youtube_service.thumbnails().set(videoId=video_id, media_body=thumbnail_media).execute()
                logging.info(f"✅ 썸네일 설정 완료.")
            except Exception as e:
                logging.error(f"❌ 썸네일 업로드 오류: {e}")

        # 2. 재생목록 추가
        for plist_title in playlists_to_add:
            try:
                pid = get_or_create_playlist(youtube_service, plist_title)
                add_video_to_playlist(youtube_service, video_id, pid)
            except Exception as pe:
                logging.error(f"❌ 재생목록 추가 실패: {pe}")
        
        # 3. 댓글 작성 및 좋아요 (comment_text가 있는 경우)
        if comment_text:
            logging.info("💬 댓글 작성을 시도합니다...")
            comment_id = insert_comment(youtube_service, video_id, comment_text)
            
            # if comment_id:
            #     # 댓글 작성 성공 시 좋아요 누르기
            #     logging.info(f"👍 댓글({comment_id})에 좋아요를 시도합니다...")
            #     time.sleep(1) # 댓글 생성 직후 API 호출 시 간혹 발생하는 레이스 컨디션 방지
            #     rate_comment(youtube_service, comment_id, 'like')

            # --- [안전 장치 2] 댓글 등록 후 대기 (2초) ---
            logging.info("⏳ 댓글 등록 확인을 위해 2초 대기 후 상태를 업데이트합니다...")
            time.sleep(2)

        # 4. 예약 상태로 전환 (우회 전략을 사용한 경우)
        if perform_schedule_update_later:
            logging.info(f"🔄 댓글 작성 완료 후, 비디오를 '예약(Private)' 상태로 전환합니다. (시간: {scheduled_publish_at})")
            try:
                youtube_service.videos().update(
                    part="status",
                    body={
                        "id": video_id,
                        "status": {
                            "privacyStatus": "private",
                            "publishAt": scheduled_publish_at
                        }
                    }
                ).execute()
                logging.info("✅ 비디오 예약 설정 업데이트 완료.")
            except Exception as e:
                logging.error(f"❌ 비디오 예약 설정 업데이트 실패 (영상은 일부공개로 남아있을 수 있음): {e}")

        return {'success': True, 'video_id': video_id}

    except googleapiclient.errors.HttpError as e:
        error_details = {
            'success': False,
            'status_code': e.resp.status,
            'message': 'YouTube API 오류 발생',
            'reason': '알 수 없음'
        }
        try:
            error_content = json.loads(e.content.decode('utf-8'))
            if 'error' in error_content and 'message' in error_content['error']:
                error_details['message'] = error_content['error']['message']
            if 'error' in error_content and 'errors' in error_content['error']:
                if error_content['error']['errors'] and 'reason' in error_content['error']['errors'][0]:
                    error_details['reason'] = error_content['error']['errors'][0]['reason']
        except (json.JSONDecodeError, KeyError):
            pass
        
        logging.error(f"❌ YouTube API 오류: {error_details}")
        return error_details
    except Exception as e:
        logging.error(f"❌ 업로드 중 예기치 않은 오류: {e}")
        return {'success': False, 'message': f"예기치 않은 오류: {e}", 'reason': 'unexpectedError'}

def generate_credentials_locally(client_secrets_file, output_credentials_file):
    """로컬 자격 증명 생성"""
    try:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
        credentials = flow.run_local_server(port=0)
        with open(output_credentials_file, 'w') as token:
            token.write(credentials.to_json())
        logging.info(f"✅ 자격 증명 생성 완료: {output_credentials_file}")
    except Exception as e:
        logging.error(f"❌ 자격 증명 생성 오류: {e}")

if __name__ == '__main__':
    print("이 스크립트는 로컬에서 credentials.json 생성용입니다.")