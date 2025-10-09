package lcc.license

default decision = {
  "status": status,
  "context": context_name,
  "chosen_license": chosen,
  "reasons": reasons,
  "alternatives": alternatives,
  "policy": policy.name,
}

policy := data.lcc.policies

contexts := policy.contexts

context_name := ctx_name {
  input.context != ""
  ctx_name := input.context
  ctx_name != null
}

context_name := ctx_name {
  (input.context == "" or not input.context) 
  policy.default_context != ""
  ctx_name := policy.default_context
}

context_name := ctx_name {
  not (input.context != "" or policy.default_context != "")
  some name
  contexts[name]
  ctx_name := name
}

context := ctx {
  ctx := contexts[context_name]
}

preference := object.get(context, "dual_license_preference", "most_permissive")
preferred_order := object.get(context, "preferred_order", [])

default_license := input.license {
  input.license
}

default_license := "UNKNOWN" {
  not input.license
}

licenses := object.get(input, "license_options", [default_license])

allow_patterns := object.get(context, "allow", [])
deny_patterns := object.get(context, "deny", [])
review_patterns := object.get(context, "review", [])
deny_reasons := object.get(context, "deny_reasons", {})
review_reasons := object.get(context, "review_reasons", {})

alternatives := [result |
  license := licenses[_]
  disp := disposition(license)
  reason := alternative_reason(license, disp)
  result := {"license": license, "disposition": disp, "reason": reason}
]

violations := [entry |
  entry := alternatives[_]
  entry.disposition == "deny"
]

warnings := [entry |
  entry := alternatives[_]
  entry.disposition == "review"
]

status := "violation" {
  count(violations) > 0
}

status := "warning" {
  count(violations) == 0
  count(warnings) > 0
}

status := "pass" {
  count(violations) == 0
  count(warnings) == 0
}

reasons := build_reasons(violations, warnings, status)

chosen := select_license(licenses)


# -------------------------------------------------------------------
# Helper rules
# -------------------------------------------------------------------

disposition(license) := "deny" {
  matches_any(deny_patterns, license)
}

disposition(license) := "allow" {
  matches_any(allow_patterns, license)
}

disposition(license) := "review" {
  not matches_any(deny_patterns, license)
  matches_any(review_patterns, license)
}

disposition(license) := "review" {
  count(allow_patterns) > 0
  not matches_any(deny_patterns, license)
  not matches_any(allow_patterns, license)
}

disposition(license) := "unknown" {
  count(allow_patterns) == 0
  not matches_any(deny_patterns, license)
  not matches_any(review_patterns, license)
}

alternative_reason(license, "deny") := reason {
  reason := matching_reason(deny_reasons, license)
}

alternative_reason(license, "review") := reason {
  reason := matching_reason(review_reasons, license)
}

alternative_reason(_, _) := null

matching_reason(map, license) := map[key] {
  some key
  map[key]
  matches(key, license)
}

matches_any(patterns, value) {
  some pattern
  patterns[_] == pattern
  matches(pattern, value)
}

matches(pattern, value) {
  glob.match(pattern, [], value)
}

build_reasons(violations, warnings, _) := reasons {
  reasons := [entry.reason | entry := violations[_]; entry.reason != null]
  count(reasons) > 0
}

build_reasons(violations, warnings, _) := reasons {
  count(violations) == 0
  reasons := [entry.reason | entry := warnings[_]; entry.reason != null]
  count(reasons) > 0
}

build_reasons(violations, warnings, "pass") := ["All discovered licenses are permitted."] {
  count(violations) == 0
  count(warnings) == 0
}

build_reasons(violations, warnings, status) := [default_message] {
  count([entry | entry := violations[_]; entry.reason != null]) == 0
  count([entry | entry := warnings[_]; entry.reason != null]) == 0
  status == "violation"
  default_message := "One or more licenses are denied by policy."
}

build_reasons(violations, warnings, status) := [default_message] {
  count(violations) == 0
  count([entry | entry := warnings[_]; entry.reason != null]) == 0
  status == "warning"
  default_message := "One or more licenses require manual review."
}


# License selection helpers ------------------------------------------------

select_license(licenses) := chosen {
  allowed := [license |
    license := licenses[_]
    disposition(license) != "deny"
  ]
  count(allowed) > 0
  chosen := choose_by_preference(allowed)
}

select_license(licenses) := licenses[0] {
  count([license | license := licenses[_]; disposition(license) != "deny"]) == 0
}

choose_by_preference(candidates) := license {
  preference == "prefer_order"
  preferred := preferred_order
  some pattern
  preferred[_] == pattern
  licenses := [candidate |
    candidate := candidates[_]
    matches(pattern, candidate)
  ]
  count(licenses) > 0
  license := licenses[0]
}

choose_by_preference(candidates) := license {
  preference == "avoid_copyleft"
  non_copyleft := [candidate |
    candidate := candidates[_]
    not is_strong_copyleft(candidate)
  ]
  count(non_copyleft) > 0
  license := non_copyleft[0]
}

choose_by_preference(candidates) := license {
  min_rank := min([license_rank(c) | c := candidates[_]])
  license := candidates[_]
  license_rank(license) == min_rank
}

license_rank(license) := rank {
  category := license_category(license)
  ranks := {
    "permissive": 0,
    "weak_copyleft": 1,
    "unknown": 2,
    "restricted": 3,
    "strong_copyleft": 4
  }
  rank := ranks[category]
}

license_category(license) := "strong_copyleft" {
  contains_any(license, ["GPL", "AGPL", "SSPL", "CDDL", "EPL", "CC-BY-SA"])
}

license_category(license) := "weak_copyleft" {
  contains_any(license, ["LGPL", "MPL", "CPL"])
}

license_category(license) := "restricted" {
  contains_any(license, ["NONCOMMERCIAL", "-NC", "NC-", "RAIL", "PROPRIETARY"])
}

license_category(license) := "permissive" {
  contains_any(license, ["MIT", "APACHE", "BSD", "ISC", "CC0"])
}

license_category(license) := "unknown" {
  not contains_any(license, ["MIT", "APACHE", "BSD", "ISC", "CC0", "GPL", "AGPL", "LGPL", "MPL", "EPL", "SSPL", "CC-BY-SA", "NONCOMMERCIAL", "RAIL", "PROPRIETARY", "CDDL", "CPL"])
}

is_strong_copyleft(license) {
  license_category(license) == "strong_copyleft"
}

contains_any(license, keywords) {
  some keyword
  keywords[_] == keyword
  lower_contains(license, keyword)
}

lower_contains(license, keyword) {
  lower := lower_ascii(license)
  lower_keyword := lower_ascii(keyword)
  contains(lower, lower_keyword)
}

# Lowercase helper using ascii transform
lower_ascii(str) := lower(str)
