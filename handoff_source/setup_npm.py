npm_content = '@ECHO OFF\nnode "C:\\Users\\Administrator\\AppData\\Roaming\\npm\\node_modules\\npm\\bin\\npm-cli.js" %*\n'
npx_content = '@ECHO OFF\nnode "C:\\Users\\Administrator\\AppData\\Roaming\\npm\\node_modules\\npm\\bin\\npx-cli.js" %*\n'

for p in [r'C:\Users\Administrator\AppData\Roaming\npm', r'C:\Program Files\nodejs']:
    with open(f'{p}\\npm.cmd', 'w', encoding='utf-8') as f:
        f.write(npm_content)
    with open(f'{p}\\npx.cmd', 'w', encoding='utf-8') as f:
        f.write(npx_content)
print('WRITTEN OK')
