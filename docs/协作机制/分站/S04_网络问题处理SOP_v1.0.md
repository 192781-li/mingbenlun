# S04网络问题处理SOP v1.0

> 分站：S04 Coq形式化分站
> 日期：2026-09-02
> 目的：标准化网络问题的识别、分类、处理和升级，避免无脑重试和重复踩坑

---

## 一、问题分类与识别

遇到git push/pull/fetch失败时，**先看错误信息，再决定处理方式**。不要无脑重试。

### 类型A：配置问题（URL/Token错误）

**错误特征**：
- `URL rejected: Malformed input to a URL function`
- `Authentication failed`
- `remote: Invalid username or password`
- `fatal: could not read Username`

**原因**：
- git remote URL格式错误（token和@之间有空格、特殊字符未转义）
- token过期或无效
- token没有写入URL

**处理步骤**：
1. 检查remote URL：`git remote -v`
2. 如果URL有空格或格式错误，重新设置：
   ```bash
   git remote set-url origin https://<token>@github.com/192781-li/mingbenlun.git
   ```
3. 验证token有效性：
   ```bash
   curl -s -H "Authorization: token <token>" https://api.github.com/user | grep login
   ```
4. 重新push/pull

**注意**：`mingxu_fix_all.sh`脚本在Windows Git Bash上可能把token和@之间加空格。运行脚本后**必须检查URL**，如果有空格手动修复。

---

### 类型B：网络连接问题（超时/连接被重置）

**错误特征**：
- `Failed to connect to github.com port 443: Could not connect to server`
- `Connection was reset`
- `Recv failure: Connection was reset`
- `Operation timed out`
- `unexpected disconnect while reading sideband packet`

**原因**：
- GitHub的443端口暂时不可达（国内网络环境常见）
- 网络波动
- DNS解析问题

**处理步骤**：
1. **第一次失败**：等待30秒，重试1次
2. **第二次失败**：检查网络连通性：
   ```bash
   ping github.com
   ```
   - 如果ping通但git连不上 → 是HTTPS/SSL问题，转类型C
   - 如果ping不通 → 是网络问题，等待2分钟后重试
3. **第三次失败**：切换到SSH方式（见第五节）
4. **第四次失败**：记录状态，联动大总站（S00），等网络恢复

**重试策略**：
- 最多重试3次
- 间隔：30秒 → 2分钟 → 5分钟
- 不要连续快速重试（会被GitHub限流）

---

### 类型C：SSL证书问题

**错误特征**：
- `schannel: next InitializeSecurityContext failed: CRYPT_E_NO_REVOCATION_CHECK`
- `SSL certificate problem: unable to get local issuer certificate`
- `SSL certificate problem: certificate has expired`

**原因**：
- Windows schannel无法访问证书吊销服务器（国内网络环境常见）
- git的SSL后端配置错误
- CA证书路径配置错误

**处理步骤**：
1. **临时方案**（紧急push时使用）：
   ```bash
   git -c http.sslVerify=false push origin <branch>
   ```
   注意：这会禁用SSL验证，仅用于紧急情况，不要全局设置。

2. **长期方案1**：切换到SSH方式（见第五节），SSH不依赖SSL证书

3. **长期方案2**：配置schannel禁用吊销检查：
   ```bash
   git config --global http.schannelCheckRevoke false
   ```
   注意：在某些Windows版本上此配置可能不生效。

4. **长期方案3**：切换到openssl后端并配置CA证书：
   ```bash
   git config --global http.sslBackend openssl
   git config --global http.sslCAInfo <path-to-cert.pem>
   ```
   PortableGit的CA证书路径通常是：`mingw64/etc/ssl/cert.pem`

---

### 类型D：push冲突（non-fast-forward）

**错误特征**：
- `Updates were rejected because the remote contains work that you do not have`
- `fetch first`
- `non-fast-forward`

**原因**：远程分支有新提交，本地没有同步。

**处理步骤**：
1. 先pull：
   ```bash
   git pull origin <branch>
   ```
2. 如果有冲突，解决冲突后commit
3. 再push

---

## 二、mingxu_fix_all.sh使用规范

### 什么时候用
- 类型A（配置问题）：脚本可以修复URL和token
- 类型D（push冲突）：脚本可以合并main
- 多种问题混合时

### 什么时候不用
- 类型B（网络连接问题）：脚本解决不了网络连接，只会浪费时间
- 类型C（SSL证书问题）：脚本可能切换SSL后端导致更多问题

### 使用后必须检查
运行`mingxu_fix_all.sh`后，**必须**：
1. 检查remote URL是否有空格：`git remote -v`
2. 如果有空格，手动修复：`git remote set-url origin <正确的URL>`
3. 检查是否创建了测试commit（`mingxu-fix-test-*`），如果有，撤销：
   ```bash
   git reset --soft HEAD~1
   ```

---

## 三、升级策略

### 什么时候联动大总站（S00）
- 类型B网络问题，重试3次+等待10分钟后仍然失败
- 类型C SSL问题，所有方案都试过仍然失败
- 需要大总站帮忙在其他环境测试push
- 需要大总站帮忙合并PR（因为本地push失败）

### 联动方式
1. 在定时任务网络配置的task_queue里添加任务，assigned_to: "S00"
2. 任务描述写清楚：什么问题、试过什么方案、错误信息是什么、需要大总站做什么
3. commit当前状态，push到GitHub（如果能push的话）
4. 如果push失败，把错误信息记录到本地文件，等网络恢复后push

---

## 四、重试策略总结

| 问题类型 | 最大重试次数 | 重试间隔 | 失败后升级 |
|---|---|---|---|
| A 配置问题 | 2次 | 立即 | 手动检查URL和token |
| B 网络连接 | 3次 | 30秒→2分钟→5分钟 | 切换SSH或联动S00 |
| C SSL证书 | 2次 | 立即 | 临时禁用验证push，长期切SSH |
| D push冲突 | 1次 | 立即 | pull后解决冲突再push |

---

## 五、SSH配置（推荐长期方案）

SSH over HTTPS（443端口）是国内网络环境下最稳定的GitHub连接方式。

### 配置步骤
1. 生成SSH key：
   ```bash
   ssh-keygen -t ed25519 -C "mingxu-S04@localhost" -f ~/.ssh/id_ed25519 -N ""
   ```

2. 把公钥添加到GitHub：
   - 打开GitHub → Settings → SSH and GPG keys → New SSH key
   - Title: `mingxu-S04`
   - Key: 粘贴`~/.ssh/id_ed25519.pub`的内容
   - 点击Add SSH key

3. 配置SSH over HTTPS（`~/.ssh/config`）：
   ```
   Host github.com
     Hostname ssh.github.com
     Port 443
     User git
     IdentityFile ~/.ssh/id_ed25519
     StrictHostKeyChecking no
   ```

4. 切换git remote到SSH：
   ```bash
   git remote set-url origin git@github.com:192781-li/mingbenlun.git
   ```

5. 测试连接：
   ```bash
   ssh -T git@github.com
   ```
   成功时显示：`Hi <username>! You've successfully authenticated, but GitHub does not provide shell access.`

### SSH的优势
- 不依赖SSL证书（避免类型C问题）
- 443端口通常比22端口更稳定（国内网络环境）
- 不需要在URL里写token（更安全）
- 一次配置，长期使用

---

## 六、经验教训记录

### 教训1：不要无脑重试
- 网络连接超时（类型B）重试3次以上没有意义，只会浪费时间
- 应该先分类问题，再决定处理方式

### 教训2：运行修复脚本后必须检查URL
- `mingxu_fix_all.sh`在Windows上会把token和@之间加空格
- 导致"Malformed input to a URL function"错误
- 运行脚本后必须`git remote -v`检查

### 教训3：SSL证书问题用临时方案应急
- `git -c http.sslVerify=false push`可以应急push
- 但不要全局设置`http.sslVerify=false`（不安全）
- 长期方案是切换到SSH

### 教训4：SSH over HTTPS是国内最稳定的方式
- SSH的22端口经常被防火墙阻止
- 配置`Port 443`和`Hostname ssh.github.com`后，SSH走443端口，通常很稳定
- 一次配置，长期受益

### 教训5：commit不会因为push失败而丢失
- push失败时，commit已经在本地了
- 不要因为push失败就慌，commit不会丢
- 等网络恢复后再push就行

---

*S04 Coq形式化分站 · 2026-09-02*
