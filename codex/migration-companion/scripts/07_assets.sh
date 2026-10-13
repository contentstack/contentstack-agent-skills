#!/usr/bin/env bash
# Assets & image transforms. (doc §10, gotchas #11,12,17)
. "$(dirname "$0")/_lib.sh"
begin "assets" "Asset URL & image-transform translation"

# Contentful asset shape residue
check "asset.fields.file.url (use asset.url)"       "\.fields\.file\."
check "protocol-relative URL fix ('https:' + url)"  "['\"]https?:['\"][[:space:]]*\+"
check "asset.fields.title/fileName (use asset.title/filename)" "\.fields\.(title|fileName|file)\b"

# Contentful image API params carried over verbatim
check "Contentful image params (?w=/&h=/fm=/fit=) in URL strings" "[?&](w|h|fm|fit|q|bg|dpr|or)="

# Verified caveat: ImageTransform is exported TYPE-ONLY at the package root.
if [ -n "$(search "new[[:space:]]+ImageTransform\(")" ]; then
  check "ImageTransform imported from package root (type-only — 'new ImageTransform()' may fail at runtime)" \
        "import[^;]*ImageTransform[^;]*@contentstack/delivery-sdk['\"]"
fi

finish
