# 县域人力资源产业园运营系统 — 业务建模文档

> 版本：v1.0 | 日期：2026-08-12 | 作者：辛特助

---

## 一、系统概述

本系统面向县域人力资源产业园，覆盖 **企业入驻、招聘服务、培训服务、岗位外包** 四大核心业务线，实现从招商入驻到服务交付的全流程数字化管理。

### 核心业务线

| 业务线 | 核心价值 | 关键闭环 |
|--------|---------|---------|
| 企业入驻 | 招商引资、园区管理 | 申请→审核→签约→入驻→考核→续约/退出 |
| 招聘服务 | 人才供需匹配 | 岗位发布→简历投递→面试→录用→入职跟踪 |
| 培训服务 | 技能提升、持证上岗 | 需求调研→课程开设→报名→培训→考核→发证 |
| 岗位外包 | 灵活用工、降本增效 | 需求对接→人员匹配→外派→管理→结算→评价 |

---

## 二、对象类型表（Object Types）

### 2.1 核心对象

| 对象类型 | 英文标识 | 说明 | 关键属性 |
|---------|---------|------|---------|
| **园区** | `Park` | 人力资源产业园实体 | id, name, address, area, contactPhone, adminOrgId, status |
| **入驻企业** | `Enterprise` | 入驻园区的企业/机构 | id, name, unifiedSocialCreditCode, industry, scale, contactPerson, contactPhone, email, address, settlementDate, status, parkId |
| **求职者** | `JobSeeker` | 在平台注册的求职者 | id, name, idCard, phone, gender, birthDate, education, major, workYears, currentAddress, expectedSalary, expectedIndustry, status |
| **岗位** | `Position` | 企业发布的招聘岗位 | id, title, enterpriseId, category, description, requirements, salaryMin, salaryMax, workAddress, headcount, urgent, status, publishDate, expireDate |
| **简历** | `Resume` | 求职者的简历 | id, jobSeekerId, targetPosition, selfIntroduction, workExperiences[], educationExperiences[], skills[], attachments[], status, updateTime |
| **培训项目** | `TrainingProgram` | 园区开设的培训课程 | id, name, category, trainer, trainerOrg, startDate, endDate, location, maxEnrollment, fee, description, certificate, status |
| **培训记录** | `TrainingRecord` | 求职者的培训参与记录 | id, programId, jobSeekerId, enrollDate, attendanceRate, examScore, certificateNo, status |
| **外包项目** | `OutsourcingProject` | 岗位外包服务项目 | id, title, enterpriseId, positionCategory, headcount, workAddress, salaryRange, duration, requirements, status |
| **外包人员** | `OutsourcedWorker` | 被外派到企业的工作人员 | id, jobSeekerId, projectId, enterpriseId, startDate, endDate, dailyRate, status, evaluation |
| **合同** | `Contract` | 各类合同/协议 | id, type, partyA, partyB, content, signDate, startDate, endDate, amount, status, attachments[] |
| **服务工单** | `ServiceTicket` | 企业服务请求/问题反馈 | id, enterpriseId, type, title, description, priority, assignee, status, createTime, resolveTime |
| **入驻申请** | `SettlementApplication` | 企业入驻申请 | id, enterpriseId, applicationDate, businessScope, expectedArea, expectedStaff, reason, attachments[], status, reviewNotes |

### 2.2 辅助对象

| 对象类型 | 英文标识 | 说明 | 关键属性 |
|---------|---------|------|---------|
| **园区管理员** | `ParkAdmin` | 园区运营管理人员 | id, name, phone, role, department, status |
| **投递记录** | `Application` | 岗位投递记录 | id, positionId, resumeId, jobSeekerId, enterpriseId, applyDate, status, interviewTime, feedback |
| **面试记录** | `Interview` | 面试安排与结果 | id, applicationId, interviewer, interviewTime, location, type, score, feedback, status |
| **评价** | `Review` | 服务评价 | id, targetType, targetId, reviewerId, score, content, createTime |
| **政策公告** | `Policy` | 政策通知/公告 | id, title, content, category, publishDate, expireDate, status |
| **统计数据** | `Statistics` | 各类统计汇总 | id, type, period, data, generateTime |

---

## 三、链接类型表（Link Types）

### 3.1 核心关系

| 链接类型 | 英文标识 | 源对象 | 目标对象 | 基数 | 说明 |
|---------|---------|-------|---------|------|------|
| **入驻于** | `settledIn` | Enterprise | Park | N:1 | 企业入驻到某个园区 |
| **发布岗位** | `publishes` | Enterprise | Position | 1:N | 企业发布招聘岗位 |
| **拥有简历** | `owns` | JobSeeker | Resume | 1:N | 求职者拥有多份简历 |
| **投递岗位** | `appliesTo` | Resume | Position | N:M | 简历投递到岗位 |
| **参与培训** | `enrollsIn` | JobSeeker | TrainingProgram | N:M | 求职者参与培训项目 |
| **外派至** | `outsourcedTo` | OutsourcedWorker | Enterprise | N:1 | 外包人员被派往企业 |
| **归属项目** | `belongsTo` | OutsourcedWorker | OutsourcingProject | N:1 | 外包人员归属外包项目 |
| **签署合同** | `signsContract` | Enterprise | Contract | 1:N | 企业签署合同 |
| **提交申请** | `submits` | Enterprise | SettlementApplication | 1:N | 企业提交入驻申请 |
| **创建工单** | `createsTicket` | Enterprise | ServiceTicket | 1:N | 企业创建服务工单 |
| **处理工单** | `handlesTicket` | ParkAdmin | ServiceTicket | 1:N | 管理员处理工单 |

### 3.2 派生关系

| 链接类型 | 英文标识 | 源对象 | 目标对象 | 基数 | 说明 |
|---------|---------|-------|---------|------|------|
| **安排面试** | `schedulesInterview` | Position | Interview | 1:N | 岗位关联面试记录 |
| **面试候选人** | `interviewsCandidate` | Interview | JobSeeker | N:1 | 面试对应求职者 |
| **评价企业** | `reviewsEnterprise` | JobSeeker | Enterprise | N:M | 求职者评价企业 |
| **评价培训** | `reviewsTraining` | JobSeeker | TrainingProgram | N:M | 学员评价培训 |
| **关联政策** | `relatesPolicy` | Policy | Enterprise | N:M | 政策面向企业 |

---

## 四、操作类型表（Action Types）

### 4.1 企业入驻流程操作

| 操作 | 英文标识 | 触发对象 | 前置条件 | 后置状态变更 | 说明 |
|------|---------|---------|---------|------------|------|
| 提交入驻申请 | `submitSettlement` | Enterprise | 企业已注册 | SettlementApplication.status = PENDING | 企业提交入驻申请 |
| 审核申请 | `reviewSettlement` | SettlementApplication | status = PENDING | status = APPROVED / REJECTED | 园区管理员审核 |
| 签署入驻合同 | `signSettlementContract` | Enterprise | 申请已批准 | Contract 创建, Enterprise.status = SETTLED | 签署入驻协议 |
| 分配办公位 | `assignWorkspace` | Enterprise | 已签约 | Enterprise.workspaceId 更新 | 分配具体办公区域 |
| 年度考核 | `annualReview` | Enterprise | status = SETTLED | 生成考核记录, 更新评级 | 年度运营考核 |
| 续约 | `renewSettlement` | Enterprise | 合同即将到期 | Contract 续签 | 合同续约 |
| 退出园区 | `exitPark` | Enterprise | 合同到期/主动退出 | Enterprise.status = EXITED | 企业退出 |

### 4.2 招聘服务流程操作

| 操作 | 英文标识 | 触发对象 | 前置条件 | 后置状态变更 | 说明 |
|------|---------|---------|---------|------------|------|
| 发布岗位 | `publishPosition` | Enterprise | status = SETTLED | Position.status = PUBLISHED | 企业发布招聘岗位 |
| 投递简历 | `submitResume` | JobSeeker | 简历已完善 | Application 创建, status = NEW | 求职者投递简历 |
| 筛选简历 | `screenResume` | Enterprise | Application.status = NEW | status = SHORTLISTED / REJECTED | 企业筛选简历 |
| 安排面试 | `scheduleInterview` | Enterprise | Application.status = SHORTLISTED | Interview 创建, status = SCHEDULED | 安排面试 |
| 记录面试结果 | `recordInterviewResult` | Interview | status = SCHEDULED | status = PASSED / FAILED | 记录面试结果 |
| 发送录用通知 | `sendOffer` | Enterprise | Interview.status = PASSED | Application.status = OFFERED | 发送录用通知 |
| 确认入职 | `confirmOnboard` | JobSeeker | Application.status = OFFERED | status = ONBOARDED | 求职者确认入职 |
| 关闭岗位 | `closePosition` | Enterprise | Position.status = PUBLISHED | status = CLOSED | 岗位招满关闭 |

### 4.3 培训服务流程操作

| 操作 | 英文标识 | 触发对象 | 前置条件 | 后置状态变更 | 说明 |
|------|---------|---------|---------|------------|------|
| 创建培训项目 | `createTraining` | ParkAdmin | — | TrainingProgram 创建, status = DRAFT | 创建培训课程 |
| 发布培训 | `publishTraining` | TrainingProgram | status = DRAFT | status = PUBLISHED | 发布培训项目 |
| 报名培训 | `enrollTraining` | JobSeeker | TrainingProgram.status = PUBLISHED | TrainingRecord 创建, status = ENROLLED | 求职者报名 |
| 签到打卡 | `checkInTraining` | TrainingRecord | status = ENROLLED | attendanceRate 更新 | 培训签到 |
| 参加考试 | `takeExam` | TrainingRecord | 培训已结束 | examScore 更新, status = EXAMINED | 参加培训考核 |
| 颁发证书 | `issueCertificate` | TrainingRecord | examScore >= 合格线 | certificateNo 生成, status = CERTIFICATED | 颁发培训证书 |
| 评价培训 | `reviewTraining` | JobSeeker | status = CERTIFICATED | Review 创建 | 学员评价 |

### 4.4 岗位外包流程操作

| 操作 | 英文标识 | 触发对象 | 前置条件 | 后置状态变更 | 说明 |
|------|---------|---------|---------|------------|------|
| 提交外包需求 | `submitOutsourcingNeed` | Enterprise | status = SETTLED | OutsourcingProject 创建, status = PENDING | 企业提交外包需求 |
| 审核需求 | `reviewOutsourcing` | ParkAdmin | OutsourcingProject.status = PENDING | status = APPROVED / REJECTED | 园区审核需求 |
| 匹配人员 | `matchWorkers` | ParkAdmin | OutsourcingProject.status = APPROVED | 匹配候选人列表 | 匹配合适人员 |
| 确认外派 | `confirmOutsourcing` | JobSeeker | 匹配完成 | OutsourcedWorker 创建, status = DISPATCHED | 人员确认外派 |
| 日常考勤 | `dailyAttendance` | OutsourcedWorker | status = DISPATCHED | 考勤记录更新 | 记录每日考勤 |
| 月度结算 | `monthlySettlement` | OutsourcingProject | 月末 | 生成结算单 | 按月结算费用 |
| 评价外包服务 | `reviewOutsourcing` | Enterprise | 结算完成 | Review 创建 | 企业评价 |
| 结束外包 | `endOutsourcing` | OutsourcingProject | 合同到期/提前终止 | OutsourcedWorker.status = RETURNED | 外包结束 |

### 4.5 通用操作

| 操作 | 英文标识 | 触发对象 | 说明 |
|------|---------|---------|------|
| 创建工单 | `createTicket` | Enterprise | 企业提交服务请求 |
| 分配工单 | `assignTicket` | ParkAdmin | 管理员分配工单 |
| 处理工单 | `resolveTicket` | ParkAdmin | 处理并关闭工单 |
| 评价服务 | `submitReview` | Enterprise / JobSeeker | 对服务进行评价 |
| 发布公告 | `publishPolicy` | ParkAdmin | 发布政策/公告 |

---

## 五、权限矩阵（Permission Matrix）

### 5.1 角色定义

| 角色 | 英文标识 | 说明 |
|------|---------|------|
| **超级管理员** | `SUPER_ADMIN` | 系统最高权限，管理园区配置 |
| **园区管理员** | `PARK_ADMIN` | 日常运营管理 |
| **招商专员** | `SETTLEMENT_OFFICER` | 负责企业入驻审核 |
| **招聘专员** | `RECRUITMENT_OFFICER` | 负责招聘服务管理 |
| **培训专员** | `TRAINING_OFFICER` | 负责培训项目管理 |
| **外包专员** | `OUTSOURCING_OFFICER` | 负责外包业务管理 |
| **企业管理员** | `ENTERPRISE_ADMIN` | 入驻企业的管理员 |
| **企业HR** | `ENTERPRISE_HR` | 企业人事专员 |
| **求职者** | `JOB_SEEKER` | 注册求职者 |
| **外包人员** | `OUTSOURCED_WORKER` | 被外派的工作人员 |

### 5.2 权限矩阵

> ✅ = 允许 | ❌ = 禁止 | 🔶 = 仅自己数据 | 📝 = 需审批

| 操作 \ 角色 | SUPER_ADMIN | PARK_ADMIN | SETTLEMENT_OFFICER | RECRUITMENT_OFFICER | TRAINING_OFFICER | OUTSOURCING_OFFICER | ENTERPRISE_ADMIN | ENTERPRISE_HR | JOB_SEEKER | OUTSOURCED_WORKER |
|------------|:-----------:|:----------:|:------------------:|:-------------------:|:----------------:|:-------------------:|:----------------:|:-------------:|:----------:|:-----------------:|
| **企业入驻** |
| 提交入驻申请 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | 🔶 | ❌ | ❌ | ❌ |
| 审核入驻申请 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 签署入驻合同 | ✅ | ✅ | 📝 | ❌ | ❌ | ❌ | 🔶 | ❌ | ❌ | ❌ |
| 查看入驻企业列表 | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 | 🔶 | ❌ | ❌ |
| 年度考核 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **招聘服务** |
| 发布岗位 | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| 投递简历 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| 筛选简历 | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| 安排面试 | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| 记录面试结果 | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| 发送录用通知 | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| 查看岗位列表 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **培训服务** |
| 创建培训项目 | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 发布培训 | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 报名培训 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| 签到打卡 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔶 | ❌ |
| 颁发证书 | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 查看培训列表 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **岗位外包** |
| 提交外包需求 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| 审核外包需求 | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 匹配人员 | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 确认外派 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔶 | 🔶 |
| 月度结算 | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | 🔶 | ❌ | ❌ | ❌ |
| 查看外包项目 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | 🔶 |
| **通用** |
| 创建工单 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 处理工单 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 发布公告 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 查看统计数据 | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 | 🔶 | 🔶 | ❌ | ❌ |

---

## 六、闭环流程（Closed-Loop Processes）

### 6.1 企业入驻闭环

```
┌─────────────────────────────────────────────────────────────────────┐
│                        企业入驻闭环                                  │
│                                                                     │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐         │
│  │ 招商 │───▶│ 申请 │───▶│ 审核 │───▶│ 签约 │───▶│ 入驻 │         │
│  │ 宣传 │    │ 提交 │    │ 审批 │    │ 合同 │    │ 分配 │         │
│  └──────┘    └──────┘    └──────┘    └──────┘    └──────┘         │
│      ▲                                              │              │
│      │              ┌──────┐    ┌──────┐            │              │
│      └──────────────│ 续约 │◀───│ 考核 │◀───────────┘              │
│         通过        │ /退出│    │ 评估 │                           │
│                     └──────┘    └──────┘                           │
└─────────────────────────────────────────────────────────────────────┘

闭环验证点：
- 每个入驻企业都有完整的申请→审核→签约记录
- 合同到期前30天自动提醒续约
- 年度考核覆盖率 = 100%
- 退出企业完成所有清算
```

### 6.2 招聘服务闭环

```
┌─────────────────────────────────────────────────────────────────────┐
│                        招聘服务闭环                                  │
│                                                                     │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐         │
│  │ 岗位 │───▶│ 简历 │───▶│ 面试 │───▶│ 录用 │───▶│ 入职 │         │
│  │ 发布 │    │ 投递 │    │ 安排 │    │ 通知 │    │ 跟踪 │         │
│  └──────┘    └──────┘    └──────┘    └──────┘    └──────┘         │
│      ▲                                              │              │
│      │              ┌──────┐    ┌──────┐            │              │
│      └──────────────│ 关闭 │◀───│ 评价 │◀───────────┘              │
│         招满        │ 岗位 │    │ 反馈 │                           │
│                     └──────┘    └──────┘                           │
└─────────────────────────────────────────────────────────────────────┘

闭环验证点：
- 每个岗位都有明确的关闭原因（招满/过期/撤回）
- 投递→面试→录用的转化率可追踪
- 入职30天内跟踪反馈
- 未录用候选人有反馈记录
```

### 6.3 培训服务闭环

```
┌─────────────────────────────────────────────────────────────────────┐
│                        培训服务闭环                                  │
│                                                                     │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐         │
│  │ 需求 │───▶│ 课程 │───▶│ 报名 │───▶│ 培训 │───▶│ 考核 │         │
│  │ 调研 │    │ 开设 │    │ 缴费 │    │ 实施 │    │ 发证 │         │
│  └──────┘    └──────┘    └──────┘    └──────┘    └──────┘         │
│      ▲                                              │              │
│      │              ┌──────┐    ┌──────┐            │              │
│      └──────────────│ 优化 │◀───│ 评价 │◀───────────┘              │
│         改进        │ 课程 │    │ 统计 │                           │
│                     └──────┘    └──────┘                           │
└─────────────────────────────────────────────────────────────────────┘

闭环验证点：
- 培训需求调研覆盖率
- 每期培训有完整的签到记录
- 考核通过率统计
- 证书颁发可追溯
- 学员评价反馈到课程优化
```

### 6.4 岗位外包闭环

```
┌─────────────────────────────────────────────────────────────────────┐
│                        岗位外包闭环                                  │
│                                                                     │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐         │
│  │ 需求 │───▶│ 审核 │───▶│ 匹配 │───▶│ 外派 │───▶│ 管理 │         │
│  │ 对接 │    │ 评估 │    │ 人员 │    │ 入职 │    │ 考勤 │         │
│  └──────┘    └──────┘    └──────┘    └──────┘    └──────┘         │
│      ▲                                              │              │
│      │              ┌──────┐    ┌──────┐            │              │
│      └──────────────│ 结算 │◀───│ 评价 │◀───────────┘              │
│         新项目      │ 对账 │    │ 结束 │                           │
│                     └──────┘    └──────┘                           │
└─────────────────────────────────────────────────────────────────────┘

闭环验证点：
- 每个外包项目有完整的结算记录
- 外包人员考勤数据完整
- 月度结算与企业确认一致
- 项目结束有评价和人员回流记录
```

---

## 七、状态机定义

### 7.1 入驻申请状态

```
DRAFT → PENDING → APPROVED → CONTRACTED → SETTLED
                  ↘ REJECTED (可重新提交)
                  
SETTLED → ANNUAL_REVIEW → RENEWED / EXITED
```

### 7.2 岗位状态

```
DRAFT → PUBLISHED → ACTIVE → CLOSED (招满/过期/撤回)
```

### 7.3 投递状态

```
NEW → SHORTLISTED → INTERVIEWING → OFFERED → ONBOARDED
  ↘ REJECTED (可标记人才库)
```

### 7.4 培训项目状态

```
DRAFT → PUBLISHED → ENROLLING → IN_PROGRESS → COMPLETED → ARCHIVED
```

### 7.5 外包项目状态

```
PENDING → APPROVED → MATCHING → IN_PROGRESS → SETTLING → COMPLETED
        ↘ REJECTED
```

---

## 八、数据流转关系图

```
                    ┌─────────────────┐
                    │     园  区      │
                    │     Park        │
                    └────────┬────────┘
                             │ 1:N
                             ▼
┌─────────────┐      ┌─────────────────┐      ┌─────────────┐
│   政  策    │◀────▶│    入驻企业      │◀────▶│   岗  位    │
│   Policy    │      │   Enterprise    │      │  Position   │
└─────────────┘      └────────┬────────┘      └──────┬──────┘
                              │ 1:N                  │ N:M
                              ▼                      ▼
                    ┌─────────────────┐      ┌─────────────┐
                    │     合  同      │      │   简  历    │
                    │   Contract      │      │   Resume    │
                    └─────────────────┘      └──────┬──────┘
                              ▲                      │
                              │                      ▼
                    ┌─────────────────┐      ┌─────────────┐
                    │   服务工单      │      │   求职者    │
                    │ ServiceTicket   │      │  JobSeeker  │
                    └─────────────────┘      └──────┬──────┘
                              ▲                      │
                              │                      │ N:M
                              │                      ▼
                    ┌─────────────────┐      ┌─────────────┐
                    │   园区管理员    │      │  培训项目   │
                    │   ParkAdmin     │      │ Training    │
                    └─────────────────┘      └─────────────┘
```

---

## 九、关键业务规则

### 9.1 企业入驻规则

| 规则编号 | 规则描述 |
|---------|---------|
| R-001 | 企业必须提供有效的统一社会信用代码 |
| R-002 | 入驻申请需园区管理员审批，审批时限 3 个工作日 |
| R-003 | 合同期限最短 1 年，最长 5 年 |
| R-004 | 合同到期前 60 天系统自动提醒续约 |
| R-005 | 年度考核不合格企业进入观察期，连续两年不合格强制退出 |

### 9.2 招聘服务规则

| 规则编号 | 规则描述 |
|---------|---------|
| R-101 | 岗位发布需企业已入驻且状态正常 |
| R-102 | 岗位有效期最长 90 天，到期自动关闭 |
| R-103 | 求职者同一岗位 30 天内不可重复投递 |
| R-104 | 面试安排需提前 24 小时通知候选人 |
| R-105 | 录用结果需在面试后 7 个工作日内反馈 |

### 9.3 培训服务规则

| 规则编号 | 规则描述 |
|---------|---------|
| R-201 | 培训项目需至少提前 7 天发布 |
| R-202 | 报名人数不足 10 人可取消培训 |
| R-203 | 出勤率低于 70% 不予颁发证书 |
| R-204 | 考核成绩 60 分以上为合格 |
| R-205 | 证书编号全局唯一，格式：TR-YYYYMMDD-XXXX |

### 9.4 岗位外包规则

| 规则编号 | 规则描述 |
|---------|---------|
| R-301 | 外包项目需园区审核通过后方可执行 |
| R-302 | 外包人员需签署三方协议 |
| R-303 | 月度结算需在次月 5 日前完成对账 |
| R-304 | 外包人员考勤数据作为结算依据 |
| R-305 | 项目结束后外包人员自动回流人才库 |

---

## 十、统计指标

### 10.1 运营指标

| 指标名称 | 计算方式 | 统计周期 |
|---------|---------|---------|
| 入驻企业数 | COUNT(Enterprise WHERE status = SETTLED) | 实时 |
| 企业续约率 | 续约企业数 / 到期企业数 × 100% | 年度 |
| 岗位发布数 | COUNT(Position WHERE status = PUBLISHED) | 月度 |
| 招聘成功率 | 录用人数 / 面试人数 × 100% | 月度 |
| 培训参与人次 | COUNT(TrainingRecord WHERE status = CERTIFICATED) | 月度 |
| 外包项目数 | COUNT(OutsourcingProject WHERE status = IN_PROGRESS) | 实时 |
| 工单处理时效 | AVG(resolveTime - createTime) | 月度 |

### 10.2 服务指标

| 指标名称 | 计算方式 | 目标值 |
|---------|---------|-------|
| 入驻审核时效 | AVG(审核完成时间 - 提交时间) | ≤ 3 工作日 |
| 岗位匹配率 | 有投递岗位数 / 发布岗位数 × 100% | ≥ 60% |
| 培训满意度 | AVG(培训评价分数) | ≥ 4.0/5.0 |
| 工单解决率 | 已解决工单数 / 总工单数 × 100% | ≥ 95% |

---

## 附录 A：术语表

| 术语 | 定义 |
|------|------|
| 入驻企业 | 与园区签署入驻协议，在园区内办公的企业 |
| 岗位外包 | 企业将部分岗位委托给园区招聘和管理用工形式 |
| 培训证书 | 完成培训并通过考核后颁发的证明文件 |
| 服务工单 | 企业向园区提交的服务请求或问题反馈 |
| 人才库 | 已注册但未匹配岗位的求职者集合 |

---

## 附录 B：接口清单（预留）

| 接口名称 | 方向 | 说明 |
|---------|------|------|
| 社保系统对接 | 出站 | 同步参保信息 |
| 就业系统对接 | 出站 | 上报就业数据 |
| 短信通知 | 出站 | 面试通知、培训提醒 |
| 支付接口 | 入站 | 培训缴费、外包结算 |
| 电子签章 | 出站 | 合同在线签署 |

---

*文档结束*
