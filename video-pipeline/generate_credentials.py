"""1회성 스크립트: client_secret.json으로 OAuth 인증을 진행해 credentials.json을 생성한다.
브라우저가 자동으로 열리며, 채널 소유 계정(silvernatural2@gmail.com)으로 로그인/동의하면 완료된다.
"""

from youtube_upload import generate_credentials_locally

generate_credentials_locally("client_secret.json", "credentials.json")
