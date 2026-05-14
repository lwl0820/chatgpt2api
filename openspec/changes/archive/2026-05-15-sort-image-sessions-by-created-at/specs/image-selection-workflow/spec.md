## MODIFIED Requirements

### Requirement: Image selection sessions
系统 SHALL 提供选图工作流，用户可以围绕单个提示词、图片生成配置、候选队列长度和连续失败暂停阈值创建并恢复本地选图会话。系统 SHALL 只按会话 `updatedAt` 倒序列出选图会话；`updatedAt` 只表示会话创建或会话配置被用户编辑的时间，不表示会话内生图任务或候选图状态变化时间。

#### Scenario: 创建选图会话
- **WHEN** 用户在选图页输入非空提示词并开始选图
- **THEN** 系统 SHALL 创建一个选图会话，包含提示词、图片尺寸、队列长度、连续失败暂停阈值、空候选列表和运行状态
- **AND** 系统 SHALL 将该会话的 `createdAt` 和 `updatedAt` 设置为创建时间

#### Scenario: 恢复已有选图会话
- **WHEN** 用户打开此前创建的选图会话
- **THEN** 系统 SHALL 从本地存储恢复该会话的提示词、候选图、保留图片、丢弃图片和当前状态

#### Scenario: 按更新时间倒序列出会话
- **WHEN** 系统展示选图会话列表
- **THEN** 系统 SHALL 按 `updatedAt` 倒序排列会话，使最新创建或最新配置编辑的会话位于最上方

#### Scenario: 编辑会话配置会更新排序时间
- **WHEN** 用户编辑选图会话的标题、提示词、队列长度或连续失败暂停阈值并保存
- **THEN** 系统 SHALL 更新该会话的 `updatedAt`
- **AND** 会话列表 SHALL 根据新的 `updatedAt` 重新排序

#### Scenario: 生图任务变化不更新排序时间
- **WHEN** 选图会话内的候选图任务轮询、完成、失败、保留、丢弃、撤销、暂停或继续发生变化
- **THEN** 系统 SHALL 保持该会话的 `updatedAt` 不变
- **AND** 系统 SHALL NOT 因这些变化将该会话移动到比其他更新会话更靠上的位置

#### Scenario: 删除当前会话后选择下一项
- **WHEN** 用户删除当前选中的选图会话且仍有其他会话存在
- **THEN** 系统 SHALL 选择剩余会话中按 `updatedAt` 倒序排列后的第一项
