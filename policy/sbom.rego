package hotpass

default allow = false

allow {
  input.metadata.component.name == "hotpass"
  input.components[_]
}

violation[msg] {
  not allow
  msg := "SBOM missing Hotpass component entry"
}
