Describe 'Placeholder' {

    It 'Should not throw an error' -Skip:(![bool](Get-Command git -EA SilentlyContinue)) {
        { $true } | Should -Not -Throw
    }

}
