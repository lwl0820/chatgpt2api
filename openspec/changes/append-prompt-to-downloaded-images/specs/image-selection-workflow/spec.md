## MODIFIED Requirements

### Requirement: Candidate decision controls
图片选择页面 SHALL 将当前 ready 候选图展示为主要大图，并提供键盘快捷键和可见操作按钮，用于保留、丢弃、撤销和下载当前候选图。

#### Scenario: 通过键盘保留候选图
- **WHEN** ready 候选图处于 review 焦点状态，且用户在文本输入框之外按下 ArrowUp
- **THEN** 系统 SHALL 将当前候选图标记为 kept，并在存在下一张 ready 候选图时前进到下一张

#### Scenario: 通过键盘丢弃候选图
- **WHEN** ready 候选图处于 review 焦点状态，且用户在文本输入框之外按下 ArrowDown
- **THEN** 系统 SHALL 将当前候选图标记为 discarded，并在存在下一张 ready 候选图时前进到下一张

#### Scenario: 通过按钮保留或丢弃候选图
- **WHEN** 用户点击当前 ready 候选图的可见保留或丢弃按钮
- **THEN** 系统 SHALL 执行与对应键盘快捷键相同的决策动作

#### Scenario: 撤销最近一次决策
- **WHEN** 用户在保留或丢弃候选图后，在文本输入框之外按下 ArrowLeft 或点击可见撤销控件
- **THEN** 系统 SHALL 将最近一次 kept 或 discarded 候选图恢复为 ready 状态，并将其设为当前 review 候选图

#### Scenario: 撤销历史有上限
- **WHEN** 用户在一个选择 session 中执行超过十次保留或丢弃决策
- **THEN** 系统 SHALL 仅保留最近十次决策用于撤销

#### Scenario: 撤销不改动物理文件
- **WHEN** 用户撤销一次保留或丢弃决策
- **THEN** 系统 SHALL 只更新选择 session 状态，并且 SHALL NOT 创建、删除或恢复物理图片文件

#### Scenario: 下载当前候选图
- **WHEN** ready 候选图处于 review 焦点状态，且用户在文本输入框之外按下 ArrowRight 或点击可见下载控件
- **THEN** 系统 SHALL 下载当前候选图，在提示词追加设置启用且选择 session 提示词非空时将该提示词追加到下载文件数据末尾，同时使用与显式 keep 操作相同的决策历史语义将该候选图标记为 kept，并在存在下一张 ready 候选图时前进到下一张

#### Scenario: 候选队列使用缩略图
- **WHEN** 候选图显示在普通或沉浸式候选队列中
- **THEN** 系统 SHALL 在可用时使用缩略图 URL，同时保持主要 review 图和沉浸式 review 图使用完整分辨率

#### Scenario: 预加载后续原图
- **WHEN** ready 候选图被选中用于 review，且后续还存在其他 ready 候选图
- **THEN** 系统 SHALL 预加载少量有上限的后续原图，以降低主要 review 图切换延迟，同时不得在候选队列中渲染完整分辨率图片

#### Scenario: 主要图片加载状态可见
- **WHEN** 主要 review 图或沉浸式 review 图正在加载其原图
- **THEN** 系统 SHALL 显示加载提示，直到原图加载完成或失败，并且不得改变候选图状态或决策历史
