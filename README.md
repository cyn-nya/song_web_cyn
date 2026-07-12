# 音乐爬虫 + 信息网站 + 数据分析 —— 完整项目

本项目对应「爬虫与信息系统」大作业，包含三部分：

```
project/
├── crawler/        # 第一部分：爬虫
│   ├── utils.py
│   ├── crawl_singers.py
│   ├── crawl_songs.py
│   ├── requirements.txt
│   └── data/        # 运行后自动生成：singers.jsonl / songs.jsonl / images/
├── webapp/         # 第二部分：Django 网站
│   ├── manage.py
│   ├── webapp_config/     # 项目配置
│   ├── music/             # 应用：models / views / urls / templates
│   ├── static/css/style.css
│   └── requirements.txt
├── analysis/       # 第三部分：数据分析
│   └── analyze.py
└── README.md        # 本文件
```

下面是**从零开始**、假设你只有一台 Windows 电脑和装好的 VS Code 的完整操作步骤。

---

## 第 0 步：你需要先装好的东西

1. **Python**（3.10 及以上都行）
2. **VS Code 的 Python 插件**
3. **Git**（用于代码版本管理，作业要求）

---

## 第 1 步：安装 Python

1. 打开 <https://www.python.org/downloads/windows/>，下载最新的 "Windows installer (64-bit)"。
2. 运行安装包时，**一定要勾选底部的 "Add python.exe to PATH"**，然后点 "Install Now"。
3. 安装完成后，打开 VS Code，按下 `` Ctrl+` `` 打开内置终端（默认是 PowerShell），输入：
   ```powershell
   python --version
   ```
   如果显示类似 `Python 3.12.3`，说明装好了。

   > 如果提示"找不到命令"，重启一下 VS Code（有时是 PATH 没刷新），还不行就重启电脑。

---

## 第 2 步：安装 Git，并配置好

1. 下载：<https://git-scm.com/download/win>，一路默认选项安装即可。
2. 装完后在 VS Code 终端里执行（把名字/邮箱换成你自己的）：
   ```powershell
   git --version
   git config --global user.name "你的名字"
   git config --global user.email "你的邮箱@example.com"
   ```
3. 建议在 GitHub 上创建一个私有仓库（Private repository），后面把代码 push 上去，方便助教检查提交历史。

---

## 第 3 步：把项目文件放到你的电脑上

1. 在你想放作业的地方（比如 `D:\homework\`）新建一个文件夹，例如 `D:\homework\music-crawler`。
2. 把我给你的 `project` 文件夹里的所有内容（`crawler/`、`webapp/`、`analysis/`、`README.md`、`.gitignore`）复制进去。
3. 用 VS Code 打开这个文件夹：菜单栏 `文件 -> 打开文件夹...`，选中 `music-crawler` 文件夹。

---

## 第 4 步：创建虚拟环境（强烈建议，避免污染系统 Python）

在 VS Code 终端里（确保当前路径是你的项目根目录，可以用 `cd` 切换）：

```powershell
python -m venv venv
```

这会在项目里创建一个 `venv` 文件夹。然后激活它：

```powershell
.\venv\Scripts\Activate.ps1
```

激活成功后，命令行前面会出现 `(venv)` 字样。

> 如果 PowerShell 报错说"无法加载文件，因为在此系统上禁止运行脚本"，执行一次：
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
> 输入 `Y` 确认，再重新运行激活命令。

之后每次在这个项目里干活，都要先激活虚拟环境（VS Code 有时会自动帮你激活，看到终端提示里有 `(venv)` 就说明是激活状态）。

---

## 第 5 步：跑爬虫

```powershell
cd crawler
pip install -r requirements.txt
python crawl_singers.py --target 120
python crawl_songs.py --per-singer 25 --total 2100
```

- `crawl_singers.py` 会现在 `crawler/data/singers.jsonl` 里追加一行行歌手信息，并把图片存到 `crawler/data/images/`。
- `crawl_songs.py` 依赖上一步的结果，对每个歌手爬歌曲详情 + 歌词，同样是**边爬边写文件**，中途 `Ctrl+C` 停掉也没事，`crawler/data/checkpoint.json` 记录了进度，重新运行会跳过已经爬过的部分，接着爬。

**如果一直报错 / 被目标网站限制访问**，常见原因和处理办法：
- 网络问题：确认电脑能正常访问 `https://music.163.com`。
- 接口返回空或者 403：这是老接口，个别地区/时间可能被限制，可以尝试：
  - 在 `crawler/utils.py` 的 `USER_AGENTS` 列表里再加几个真实浏览器的 UA；
  - 把 `polite_sleep()` 的间隔调大一点（比如改成 2~4 秒），减小被识别为爬虫的概率；
  - 如果这个站彻底不行，作业允许换一个音乐网站爬（比如酷我音乐、QQ音乐），思路不变，只是需要重新分析对方的接口/页面结构（用浏览器 F12 开发者工具，参考文档里"API获取列表"那一节的方法）。
- 想直接检查爬到多少条数据：
  ```powershell
  python -c "print(sum(1 for _ in open('data/songs.jsonl', encoding='utf-8')))"
  python -c "print(sum(1 for _ in open('data/singers.jsonl', encoding='utf-8')))"
  ```

跑完之后确认：`crawler/data/songs.jsonl` 行数 ≥ 2000，`crawler/data/singers.jsonl` 行数 ≥ 100。

---

## 第 6 步：把爬到的数据导入网站数据库

```powershell
cd ..\webapp
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py import_data
```

`import_data` 是我写好的管理命令，会自动读取 `crawler/data/*.jsonl`，把歌手/歌曲写入 `webapp/db.sqlite3`，并把图片拷贝到 `webapp/media/images/`。

---

## 第 7 步：启动网站，本地查看效果

```powershell
python manage.py runserver
```

终端会显示一行 `Starting development server at http://127.0.0.1:8000/`，按住 `Ctrl` 点这个链接（或者直接在浏览器打开 `http://127.0.0.1:8000/`）即可看到：

- `/` 或 `/songs/`：歌曲列表页（分页）
- `/songs/<id>/`：歌曲详情页（歌词 + 评论）
- `/singers/`：歌手列表页（分页）
- `/singers/<id>/`：歌手详情页（简介 + 该歌手的歌曲）
- `/search/?q=xxx&type=song`：搜索结果页

停止服务器：终端里按 `Ctrl+C`。

（可选）如果想用 Django 自带的后台管理系统看数据库里的内容：
```powershell
python manage.py createsuperuser   # 按提示设置一个用户名密码
python manage.py runserver
```
然后访问 `http://127.0.0.1:8000/admin/` 登录查看。

---

## 第 8 步：跑数据分析，生成图表

```powershell
cd ..\analysis
pip install jieba matplotlib numpy
python analyze.py
```

运行完，图表会出现在 `analysis/output/` 文件夹里（3 张 PNG）。终端里也会打印出对应的结论数字。

打开每张图看看是否合理，然后把这三张图 + 你自己的文字解读整理进实验报告（或单独写一份"数据分析报告"）。

**注意**：脚本里默认给出的三个结论（歌手长尾分布 / 歌词长度分布 / 高频词）只是**示例**，作业要求结论要"有一定深度和启发意义"。建议你在这个基础上，结合自己爬到的数据再深入想一想，比如：
- 不同风格/年代歌手的歌词长度是否有系统性差异？
- 某几个高频词是否和平台的整体曲风（比如爬的是华语流行还是说唱）相关？
- 歌曲图片颜色、歌手简介长度和收录歌曲数是否有关联？

---

## 第 9 步：用 Git 提交代码

回到项目根目录（`music-crawler`）：

```powershell
cd ..
git init
git add .
git commit -m "init: 爬虫+网站+分析 初始版本"
```

之后每完成一个小功能就提交一次，例如：
```powershell
git add .
git commit -m "feat: 实现歌曲详情页评论功能"
```

如果要推到 GitHub：
```powershell
git remote add origin https://github.com/你的用户名/仓库名.git
git branch -M main
git push -u origin main
```

---

## 第 10 步：写实验报告，导出 PDF

用 Word / 飞书文档 / Markdown 都行，内容参考文档里"实验报告"部分的要求（系统功能介绍、数据量、技术栈、可选的时间估计与感想），最后导出成 PDF 提交。

---

## 快速排错清单

| 现象 | 可能原因 / 解决办法 |
|---|---|
| `python` 命令找不到 | 安装 Python 时没勾选 "Add to PATH"，重装一次并勾选 |
| PowerShell 不让激活虚拟环境 | 执行 `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| `pip install` 很慢或超时 | 换清华源：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| 网页图片不显示 | 确认已经跑过 `python manage.py import_data`，且 `webapp/media/images/` 下确实有文件 |
| 爬虫一直被拒绝访问 | 调大爬取间隔、换 UA、换目标网站（详见第5步说明） |
| 中文乱码/图表里中文变成方框 | Windows一般自带"微软雅黑"字体，`analyze.py`里已经配置好了；如果还是不行，检查一下电脑字体名称是否叫别的名字 |
