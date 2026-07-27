# Git Setup for CDQAI 2.0.2

Run these commands from the extracted project root.

```powershell
git init
git branch -M main
git add .
git status
git commit -m "Release CDQAI 2.0.2"
git tag -a v2.0.2 -m "CDQAI Version 2.0.2"
```

Then create an empty remote repository and connect it:

```powershell
git remote add origin <REMOTE-REPOSITORY-URL>
git push -u origin main
git push origin v2.0.2
```

`config/config.yaml`, runtime outputs, caches, logs, the virtual environment, and IDE files are intentionally excluded by `.gitignore`.
