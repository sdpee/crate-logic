TAG_TO_RELEASE = {
    "TAG-STEPH": "784629",
}

def resolve_release_id(tag_uid: str):
    return TAG_TO_RELEASE.get(tag_uid)
