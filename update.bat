@echo off
echo 🚀 Step 1: 正在同步真实图片房源...
python test_crawl.py

echo ☁️ Step 2: 正在发布至 GitHub...
:: 强制将文件加入暂存区
git add index.html listings.json update.bat test_crawl.py
git commit -m "Fix images, language sync, and wording: %date% %time%"

:: 强制推送到 master 分支
git push origin master -f

echo ✅ 发布完成！请刷新网站查看最新房源与翻译。
pause