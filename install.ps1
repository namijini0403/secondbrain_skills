# install.ps1 — second brain / 교육과정 KB 설치기 (Windows)
# 사용법:
#   .\install.ps1 -Target "C:\Users\me\Documents\my-brain"                       # 개인 second brain
#   .\install.ps1 -Target "..." -Kind curriculum-kb                              # 교육과정 지식그래프
#   .\install.ps1 -Target "..." -Kind kg-research                                # 연구용(논문) 하네스
#   .\install.ps1 -Target "..." -WithSecurity                                    # 학교앱 보안 팩 포함
param(
    [Parameter(Mandatory = $true)] [string]$Target,
    [ValidateSet("second-brain", "curriculum-kb", "kg-research")] [string]$Kind = "second-brain",
    [switch]$WithSecurity
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Copy-IfMissing($From, $To) {
    # 기존 파일은 절대 덮어쓰지 않는다 (재실행 안전)
    Get-ChildItem -Recurse -File $From | ForEach-Object {
        $rel = $_.FullName.Substring($From.Length).TrimStart('\', '/')
        $dest = Join-Path $To $rel
        if (Test-Path $dest) {
            Write-Host "  skip (이미 있음): $rel" -ForegroundColor DarkGray
        } else {
            New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
            Copy-Item $_.FullName $dest
            Write-Host "  + $rel" -ForegroundColor Green
        }
    }
}

Write-Host "`n== secondbrain_skills 설치: $Kind → $Target ==" -ForegroundColor Cyan
New-Item -ItemType Directory -Force $Target | Out-Null

# 1) 위키 템플릿
Copy-IfMissing (Join-Path $Root "templates\$Kind") $Target

# 2) 문서 추출 스킬 (모든 종류 공통)
Copy-IfMissing (Join-Path $Root "skills\extract-documents") (Join-Path $Target ".claude\skills\extract-documents")

# 3) (선택) 학교앱 보안 팩
if ($WithSecurity) {
    Copy-IfMissing (Join-Path $Root "security\agents") (Join-Path $Target ".claude\agents")
    $secSkill = Join-Path $Target ".claude\skills\school-app-security"
    New-Item -ItemType Directory -Force $secSkill | Out-Null
    if (-not (Test-Path (Join-Path $secSkill "SKILL.md"))) {
        Copy-Item (Join-Path $Root "security\SKILL.md") (Join-Path $secSkill "SKILL.md")
        Write-Host "  + .claude\skills\school-app-security\SKILL.md" -ForegroundColor Green
    }
}

Write-Host "`n설치 완료. 다음 단계:" -ForegroundColor Cyan
Write-Host "  1. (권장) pip install olefile pypdf defusedxml   # HWP/PDF 추출용"
Write-Host "  2. 소스 파일을 $Target\10-sources\ 에 넣기"
Write-Host "  3. cd `"$Target`" ; claude   실행 후:"
if ($Kind -eq "second-brain") { Write-Host "  4. /setup  (첫 실행 인터뷰) → /ingest <파일명>" }
elseif ($Kind -eq "curriculum-kb") { Write-Host "  4. /ingest <별책 파일명>  (성취기준 → 개념 원자 분해)" }
else { Write-Host "  4. CLAUDE.md §8 '시작하기'를 따라 스키마·코드북부터 작성" }
