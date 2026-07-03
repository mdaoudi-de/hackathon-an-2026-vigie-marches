# Smoke test des sources de donnees du projet (APIs publiques + serveurs MCP).
# Usage : ./scripts/test-sources.ps1

$ErrorActionPreference = 'Continue'
$results = @()

function Test-Get {
    param([string]$Name, [string]$Url)
    try {
        $r = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 20 -UseBasicParsing `
            -Headers @{ 'User-Agent' = 'hackathon-2026-transparence-marches-publics' }
        $script:results += [pscustomobject]@{ Source = $Name; Statut = $r.StatusCode; OK = $true }
    } catch {
        $script:results += [pscustomobject]@{ Source = $Name; Statut = "$($_.Exception.Message)".Substring(0, [Math]::Min(60, "$($_.Exception.Message)".Length)); OK = $false }
    }
}

function Test-Mcp {
    param([string]$Name, [string]$Url)
    $body = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke-test","version":"0.1"}}}'
    try {
        $r = Invoke-WebRequest -Uri $Url -Method POST -TimeoutSec 20 -UseBasicParsing -Body $body `
            -ContentType 'application/json' `
            -Headers @{ 'Accept' = 'application/json, text/event-stream' }
        $ok = $r.Content -match 'serverInfo'
        $script:results += [pscustomobject]@{ Source = "MCP $Name"; Statut = $r.StatusCode; OK = $ok }
    } catch {
        $script:results += [pscustomobject]@{ Source = "MCP $Name"; Statut = "$($_.Exception.Message)".Substring(0, [Math]::Min(60, "$($_.Exception.Message)".Length)); OK = $false }
    }
}

Write-Host "`n--- Serveurs MCP (.mcp.json) ---"
Test-Mcp 'parlement'      'https://parlement.tricoteuses.fr/mcp'
Test-Mcp 'datagouv'       'https://mcp.data.gouv.fr/mcp'
Test-Mcp 'justicelibre'   'https://justicelibre.org/mcp'
Test-Mcp 'service-public' 'https://mcp-service-public.nhaultcoeur.workers.dev/mcp'

Write-Host "--- APIs sans authentification ---"
Test-Get 'Tricoteuses openapi.json'    'https://parlement.tricoteuses.fr/openapi.json'
Test-Get 'Tricoteuses HATVP (lobbying)' 'https://parlement.tricoteuses.fr/representantsInterets/json?page=1&perPage=1'
Test-Get 'Canutes PostgREST (SIREN)'   'https://db.code4code.eu/canutes/services?data-%3E%3Esiren=eq.216500470&select=id,data-%3E%3Enom'
Test-Get 'Recherche entreprises'       'https://recherche-entreprises.api.gouv.fr/search?q=552032534'
Test-Get 'BODACC (annonces SIREN)'     'https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records?where=registre%20like%20%22552032534%22&limit=1'
Test-Get 'DECP tabulaire (par SIRET)'  'https://tabular-api.data.gouv.fr/api/resources/22847056-61df-452d-837d-8b8ceadbfc52/data/?titulaire_id__exact=75058171200015&page_size=1'
Test-Get 'BOAMP (dernieres annonces)'  'https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records?limit=1&order_by=dateparution%20desc'
Test-Get 'APProch (projets d''achats)' 'https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/projets-dachats-publics/records?limit=1'
Test-Get 'Gels des avoirs (DG Tresor)' 'https://gels-avoirs.dgtresor.gouv.fr/ApiPublic/api/v1/publication/derniere-publication-fichier-json'
Test-Get 'EDES / OpenSanctions miroir' 'https://data.opensanctions.org/datasets/latest/eu_edes/targets.simple.csv'

$results | Format-Table -AutoSize
$ko = @($results | Where-Object { -not $_.OK })
if ($ko.Count -eq 0) {
    Write-Host "Toutes les sources repondent." -ForegroundColor Green
} else {
    Write-Host "$($ko.Count) source(s) en echec." -ForegroundColor Yellow
    exit 1
}
