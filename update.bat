@echo off
echo 🚀 Step 1: 正在同步最新房源数据...
python test_crawl.py

echo ☁️ Step 2: 正在发布至 GitHub...
:: 强制修正远程仓库地址
git remote set-url origin https://github.com/Martin62300/havennest.git

:: 全量添加所有文件和文件夹
git add .
git commit -m "Final fix for branch sync and UI: %date% %time%"

:: 🚀 核心修正：将本地 master 分支推送到远程 main 分支
git push origin master:main -f

echo ✅ 任务完成！GitHub 上的 index.html 和 .github 文件夹现在应该出现了。
pause