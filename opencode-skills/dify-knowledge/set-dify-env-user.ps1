[System.Environment]::SetEnvironmentVariable("DIFY_API_BASE_URL", "http://hdpd.cpolar.cn/v1", "User")
[System.Environment]::SetEnvironmentVariable("DIFY_API_KEY", "dataset-UMJU8FSM8fdPLu03IXuk13bJ", "User")
[System.Environment]::SetEnvironmentVariable("DIFY_DATASET_POLICY", "385d9d8d-0d7e-444d-b405-cf7972e7f2c0", "User")
[System.Environment]::SetEnvironmentVariable("DIFY_DATASET_INTERNAL", "fd284a4a-d394-416b-b246-ab4e036d8904", "User")

Write-Host "Dify 环境变量已写入当前用户级环境变量。"
Write-Host "请关闭并重新打开 PowerShell / cmd / 相关程序后再使用。"
Write-Host "DIFY_API_BASE_URL=$([System.Environment]::GetEnvironmentVariable('DIFY_API_BASE_URL', 'User'))"
Write-Host "DIFY_DATASET_POLICY=$([System.Environment]::GetEnvironmentVariable('DIFY_DATASET_POLICY', 'User'))"
Write-Host "DIFY_DATASET_INTERNAL=$([System.Environment]::GetEnvironmentVariable('DIFY_DATASET_INTERNAL', 'User'))"
Write-Host "DIFY_API_KEY 已设置到用户环境变量（为避免泄露，此处不回显）。"
