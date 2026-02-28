@echo off
echo 🚀 Step 1: 正在同步最新房源数据...
python test_crawl.py

echo ☁️ Step 2: 正在更新 GitHub 仓库地址并上传...
:: 自动更新远程仓库地址
git remote set-url origin https://github.com/Martin62300/havennest.git

:: 强制添加 listings.json 防止遗漏
git add index.html listings.json update.bat test_crawl.py
git commit -m "Auto-update listings: %date% %time%"

:: 推送到正确的 master 分支
git push origin master -f

echo ✅ 任务完成！网站已实时同步最新房源。
pause