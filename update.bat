@echo off
echo 🚀 Step 1: 同步最新房源...
python test_crawl.py

echo ☁️ Step 2: 修正仓库并上传...
:: 自动更新为正确的仓库地址
git remote set-url origin https://github.com/Martin62300/havennest.git

git add index.html listings.json update.bat test_crawl.py
git commit -m "Fix de-duplication and service layout: %date% %time%"

:: 推送到 master 分支
git push origin master -f

echo ✅ 发布完成！房源已更新。
pause