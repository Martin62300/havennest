@echo off
echo 🚀 Step 1: 正在同步最新房源数据...
python test_crawl.py

echo ☁️ Step 2: 正在发布至 GitHub (强制同步至 main 分支)...
:: 确保远程地址无误
git remote set-url origin https://github.com/Martin62300/havennest.git

:: 全量添加，包括 .github 文件夹
git add .
git commit -m "Fix branch sync and UI content: %date% %time%"

:: 🚀 核心修正：推送到 main 而不是 master
git push origin main -f

echo ✅ 任务完成！请稍等 1 分钟后刷新网页。
pause