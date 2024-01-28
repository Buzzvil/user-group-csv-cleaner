User group text cleaner

## Setup env (Intel Mac)
```shell script
# Tested with Python 3.9.2
$ brew install pyqt5
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -U pip
$ pip install -r requirements.txt
```

## Setup env (M1 Mac)
https://stackoverflow.com/questions/65901162/how-can-i-run-pyqt5-on-my-mac-with-m1chip 참조하여 Rosseta 2 terminal에서 non-homebrew python 사용하여 환경 구축
```shell script
$ brew install pyqt5
$ /usr/bin/python3 -m venv venv
$ source venv/bin/activate
$ pip install -U pip
$ pip install -r requirements.txt
```

## Setup env (Windows)
https://www.python.org/downloads/release/python-3911/ 에서 파이썬 설치
```shell script
$ pip install -r requirements-windows.txt
```

## Run
```shell script
$ python main.py
```
---

## Build executable app (Mac)
```shell script
# Build package
pyinstaller --hidden-import=cmath --windowed --noconfirm --icon=icon.icns --name="User Group CSV Cleaner" main.py
# Regarding --hidden-import=cmath,
# https://github.com/pyinstaller/pyinstaller/issues/5589

# Build dmg
brew install npm
sudo npm install -g create-dmg

# If you get an error about "EACCES: permission denied,
# mkdir '/usr/local/lib/node_modules/create-dmg/node_modules/fs-xattr/build'", 
# run this command instead and see 
# https://github.com/npm/npm/issues/17268#issuecomment-310167614 for more details
sudo npm install -g create-dmg --unsafe-perm=true --allow-root

create-dmg 'dist/User Group CSV Cleaner.app' dist

# If you gt an XCode error like "gyp: No Xcode or CLT version extracted!"
# try running the command below then retry the above command.
# See https://stackoverflow.com/questions/27665426/trying-to-install-bcrypt-into-node-project-node-set-up-issues
# for more information
sudo xcode-select -switch /Applications/Xcode.app/Contents/Developer/
```

## Build executable app (Windows)
바이러스로 인식되는 문제가 있어 --windowed 옵션이 빠져있다.
```shell script
pyinstaller --hidden-import=cmath --noconfirm --icon=icon.icns --name="User Group CSV Cleaner" main.py
```

## Trouble shootings
--windowed로 pyinstaller 만들면 UnicodeDecodeError가 발생하는 경우가 있는데 open함수에 encoding='utf-8' 옵션을 주어서 해결.
https://stackoverflow.com/questions/47692960/error-when-using-pyinstaller-unicodedecodeerror-utf-8-codec-cant-decode-byt

PyQt5 5.13.2, 5.14.2, 5.15.4 버전은 pyinstaller로 패키징시 문제가 있어 5.13대 버전 활용.
5.13.2, 5.14.2 -> Application not responsd. CPU 100%먹음.
5.15.4 -> 실행 자체가 안됨.

© 2021 [Buzzvil](http://www.buzzvil.com), shared under the [MIT license](http://www.opensource.org/licenses/MIT).

## Release notes

### 0.1.4 (2021-07-01)
- 로그파일 저장 위치 변경
- FilterBase를 UUIDExtractorBase로 클래스 이름 변경
- App 이름 AppDemo -> CSVCleanerApp 으로 변경
- TextFileCleaner class이름 CSVCleaner로 변경
- text_cleaner_main.py -> main.py로 파일이름 변경
- M1 mac 실행 가이드 추가

### 0.1.3 (2021-03-22)
CM 배포된 첫 번째 버전
