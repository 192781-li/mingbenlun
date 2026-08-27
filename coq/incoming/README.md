# coq/incoming/

> Workbody写的Coq代码放这里。草稿区，验证通过后合并到正式库。

## 规则
- 只有Workbody往这里写文件
- 文件名格式：`T00X_workbody.v`（定理ID_作者.v）
- 写完后push到GitHub，豆包会自动跑coqc验证
- 验证结果写到 `../results/T00X_result.md`
- 验证通过后，豆包会把代码合并到正式库
- 验证不通过，Workbody看结果修改后重新提交

## 不要做的事
- ❌ 不要修改正式库的任何文件
- ❌ 不要删除这里的文件（豆包会处理）
- ❌ 不要往 `../results/` 写文件（那是豆包的目录）
