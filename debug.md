以下是整个对话从头到尾所有调试过程的梳理，按时间顺序排列：

## 1. ModuleNotFoundError — 模块找不到
- 发现问题：直接运行 `python backend/api.py` 时找不到 `backend` 包。
- 解决思路：使用模块方式运行，确保项目根目录在 `sys.path`。
- 解决步骤：启动命令改为 `python -m backend.api`。
- 解决结果：后端正常启动，导入错误消失。

## 2. API Key 未加载
- 发现问题：LLM 调用拿到的 API Key 为 `None`。
- 解决思路：入口处调用 `load_dotenv()`，读取 `.env`。
- 解决步骤：确认 `openai_compat.py` 顶部调用 `load_dotenv()`，并检查 `.env` 配置格式。
- 解决结果：API Key 正常读取，LLM 调用成功。

## 3. openai 与 httpx 版本不兼容
- 发现问题：`openai` 导入/运行期指向 `httpx` 参数变化的错误。
- 解决思路：对齐版本，避免破坏性变更。
- 解决步骤：固定 `openai==2.21.0`、`httpx==0.28.1`，重新安装。
- 解决结果：SDK 正常工作，HTTP 请求无报错。

## 4. FAISS 在 Windows 中文路径下崩溃
- 发现问题：含中文路径的课程索引读写 `faiss.write_index/read_index` 失败。
- 解决思路：先 `os.chdir()` 到索引目录，用 ASCII 相对路径操作。
- 解决步骤：在 `store_faiss.py` 的 `save()/load()` 中用 `try/finally` 包裹 `chdir`，操作完恢复。
- 解决结果：中文路径课程可正常保存/加载索引。

## 5. DOCX 格式不支持
- 发现问题：上传 `.docx` 显示不支持，无法入库。
- 解决思路：增加 `python-docx` 解析分支。
- 解决步骤：`ingest.py` 添加 `parse_docx()`，分发处支持 `.docx`；`requirements.txt` 增加依赖。
- 解决结果：Word 文档可解析并索引。

## 6. SSE 流式输出被换行截断
- 发现问题：回答含换行时 SSE 帧被截断，前端 JSON 解析失败。
- 解决思路：每个 chunk 先 `json.dumps()`，前端 `json.loads()` 还原。
- 解决步骤：后端 SSE 输出改为单行 JSON 字符串；前端逐帧解码后拼接。
- 解决结果：含 Markdown/公式的流式输出稳定。

## 7. 练习模式多轮上下文丢失
- 发现问题：第二轮提交答案时 AI 重新出题或答非所问。
- 解决思路：用完整对话 `history` 驱动 Grader/Tutor，不依赖单独状态。
- 解决步骤：`runner.py` 练习流程传递全量 `history`，移除全局 quiz 状态。
- 解决结果：练习模式多轮对话连贯，评分准确。

## 8. LaTeX 公式不渲染
- 发现问题：`\[...]` / `\(...)` 公式在 Streamlit 中原样显示。
- 解决思路：转为 MathJax 支持的 `$$...$$` / `$...$`。
- 解决步骤：前端添加 `fix_latex()`，显示前和保存 history 前调用。
- 解决结果：公式正常渲染。

## 9. 练习/考试记录用户答案提取错误
- 发现问题：记录中的 `user_answer` 取到上一轮消息。
- 解决思路：显式传入本次 `user_message`，不再从 history 反查。
- 解决步骤：`_save_practice_record/_save_exam_record` 新增 `user_message` 参数，4 个调用点同步更新。
- 解决结果：记录中的用户答案与本次提交一致。

## 10. 当前消息重复发送给 LLM
- 发现问题：history 切片包含刚追加的当前消息，LLM 收到两份相同输入。
- 解决思路：切片排除最后一条，即用 `[-21:-1]` 而非 `[-20:]`。
- 解决步骤：前端 `send_message()/stream_chat()` 改为 `chat_history[-21:-1]`。
- 解决结果：LLM 不再重复接收当前消息。

## 11. 文件上传路径穿越
- 发现问题：上传文件名可构造 `../../evil.py` 写出工作区。
- 解决思路：`os.path.basename()` 净化文件名 + 扩展名白名单。
- 解决步骤：`api.py` 上传端点使用 `safe_filename = basename(...)`，校验后缀仅允许 `.pdf/.txt/.md/.docx`。
- 解决结果：路径穿越与非法类型上传被拦截。

## 12. 课程名路径穿越
- 发现问题：`get_workspace_path(course_name)` 直接 join，`../..` 可穿越。
- 解决思路：对 `course_name` 做 `basename` 净化并校验。
- 解决步骤：`runner.py` 中 `get_workspace_path` 校验空名、`.`、`..`，非法则抛错。
- 解决结果：课程名构路径安全，穿越面消除。

## 13. chunk.py 可能死循环
- 发现问题：`overlap >= chunk_size` 时 `start` 不前进，循环不终止。
- 解决思路：入口收敛参数并加兜底前进。
- 解决步骤：当 `overlap >= chunk_size` 时自动设置为 `chunk_size // 2`；循环内若 `next_start <= start` 强制前进一个 chunk。
- 解决结果：分块循环必定终止，不再卡死。

## 14. TXT 仅支持 UTF-8
- 发现问题：GBK/GB2312 TXT 上传解析失败，静默返回空内容。
- 解决思路：多编码回退，覆盖主流中文编码。
- 解决步骤：按 `utf-8-sig → utf-8 → gbk → latin-1` 顺序尝试读取，全部失败才报错。
- 解决结果：GBK/GB2312 文件可解析，UTF-8-BOM 也被去除 BOM。

## 15. os.chdir() 线程不安全
- 发现问题：FAISS 读写用 `os.chdir()`，并发请求互相干扰进程 CWD。
- 解决思路：用全局 `threading.Lock` 串行化 `chdir → 操作 → 恢复`。
- 解决步骤：`store_faiss.py` 顶部定义锁，在 `save()/load()` 的 `chdir` 区域加锁。
- 解决结果：并发场景索引读写稳定，无目录争用。
