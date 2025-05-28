function Get-FormattedWACMAC {
    Param(
        $LocalBoxConfig
    )
    return $LocalBoxConfig.WACMAC -replace '..(?!$)', '$&-'
}
