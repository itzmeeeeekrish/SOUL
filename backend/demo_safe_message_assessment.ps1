# Synthetic-only demo for the safe message assessment endpoint.
# Start the API first from the backend directory:
#   python -m uvicorn app.main:app --reload
#
# Then run from the repository root:
#   .\backend\demo_safe_message_assessment.ps1
#
# This script sends only synthetic example text to localhost.
# The file is intentionally ASCII-only for Windows PowerShell compatibility.

$ErrorActionPreference = "Stop"
$Endpoint = "http://127.0.0.1:8000/v1/messages/analyze"

# Reconstruct the Hindi sample from UTF-8 bytes so this script remains ASCII-only.
$HindiTextBase64 = "4KSG4KSq4KSV4KS+IOCkrOCliOCkguCklSBLWUMg4KSs4KSC4KSmIOCkueCliyDgpJzgpL7gpI/gpJfgpL7gpaQg4KSF4KSq4KSo4KS+IE9UUCBzaGFyZSDgpJXgpLDgpYfgpILgpaQ="
$HindiText = [System.Text.Encoding]::UTF8.GetString(
    [System.Convert]::FromBase64String($HindiTextBase64)
)

$Examples = @(
    @{
        Title = "Suspicious KYC and credential request"
        Text = "URGENT: Your bank KYC will expire today. Share your OTP immediately at https://example.invalid"
    },
    @{
        Title = "Safety warning / hard negative"
        Text = "Never share your OTP or PIN with anyone. Use your bank's official app."
    },
    @{
        Title = "Devanagari language guard"
        Text = $HindiText
    }
)

foreach ($Example in $Examples) {
    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor DarkCyan
    Write-Host $Example.Title -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor DarkCyan

    $Body = @{ text = $Example.Text } | ConvertTo-Json -Depth 5

    try {
        $Result = Invoke-RestMethod -Uri $Endpoint -Method Post -ContentType "application/json; charset=utf-8" -Body $Body

        Write-Host "Status: $($Result.analysis_status)"
        Write-Host "Candidate label: $($Result.candidate_label)"
        if ($Result.model_candidate_label) {
            Write-Host "Raw model candidate (debug only): $($Result.model_candidate_label)"
        }
        Write-Host "Review required: $($Result.review_required)"
        if ($Result.abstention_reason) {
            Write-Host "Abstention reason: $($Result.abstention_reason)"
        }

        if ($Result.model_scores) {
            Write-Host "Uncalibrated model scores:"
            $Result.model_scores.PSObject.Properties |
                Sort-Object Name |
                ForEach-Object {
                    Write-Host ("  {0}: {1:N4}" -f $_.Name, [double]$_.Value)
                }
        }
        else {
            Write-Host "Model score: unavailable (language guard abstained)"
        }

        Write-Host "Text indicators:"
        if ($Result.risk_indicators -and $Result.risk_indicators.Count -gt 0) {
            foreach ($Indicator in $Result.risk_indicators) {
                Write-Host ("  - {0}: {1}" -f $Indicator.code, $Indicator.title)
            }
        }
        else {
            Write-Host "  No configured indicator patterns matched."
        }

        Write-Host "Context flags:"
        if ($Result.context_flags -and $Result.context_flags.Count -gt 0) {
            foreach ($Flag in $Result.context_flags) {
                Write-Host ("  - {0}: {1}" -f $Flag.code, $Flag.title)
            }
        }
        else {
            Write-Host "  No protective-context flag matched."
        }

        Write-Host "Official guidance cards:"
        if ($Result.official_guidance -and $Result.official_guidance.Count -gt 0) {
            foreach ($Card in $Result.official_guidance) {
                Write-Host ("  - {0} - {1}" -f $Card.issuer, $Card.title)
                Write-Host ("    Source: {0}" -f $Card.source_url)
                Write-Host ("    Condition: {0}" -f $Card.condition)
            }
        }
        else {
            Write-Host "  No card matched the configured indicator rules."
        }

        Write-Host "Important note: $($Result.indicator_notice)"
        Write-Host "Retrieval: $($Result.guidance_retrieval_note)"
    }
    catch {
        Write-Host "API request failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Check that the local API is running and the historical Mendeley model artifact exists."
        throw
    }
}

Write-Host ""
Write-Host "Demo complete. These are provisional results, not proof of fraud." -ForegroundColor Green
Write-Host "No real OTP, phone number, account identifier or private message was used."
