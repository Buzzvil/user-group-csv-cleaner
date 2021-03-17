User group text cleaner

## Setup env
```shell script
# Tested with Python 3.9.2
$ brew install pyqt5
$ python3 -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

## Run
```shell script
$ python text_cleaner_main.py
```
---

## Build executable app
```shell script
# Build package
pyinstaller --hidden-import=cmath --windowed --noconfirm --icon=icon.icns --name="User Group CSV Cleaner" text_cleaner_main.py
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

# If you gt an XCode error like "gyp: No Xcode or CLT version detected!"
# try running the command below then retry the above command.
# See https://stackoverflow.com/questions/27665426/trying-to-install-bcrypt-into-node-project-node-set-up-issues
# for more information
sudo xcode-select -switch /Applications/Xcode.app/Contents/Developer/
```

## Trouble shootings
--windowed로 pyinstaller 만들면 UnicodeDecodeError가 발생하는 경우가 있는데 open함수에 encoding='utf-8' 옵션을 주어서 해결.
https://stackoverflow.com/questions/47692960/error-when-using-pyinstaller-unicodedecodeerror-utf-8-codec-cant-decode-byt

PyQt5 5.13.2, 5.14.2, 5.15.4 버전은 pyinstaller로 패키징시 문제가 있어 5.13대 버전 활용.
5.13.2, 5.14.2 -> Application not responsd. CPU 100%먹음.
5.15.4 -> 실행 자체가 안됨.

© 2021 [Buzzvil](http://www.buzzvil.com), shared under the [MIT license](http://www.opensource.org/licenses/MIT).
