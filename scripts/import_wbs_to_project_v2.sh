#!/usr/bin/env bash
set -euo pipefail

RESET=false
for arg in "$@"; do
  if [[ "$arg" == "--reset" ]]; then
    RESET=true
  fi
done

if $RESET; then
  echo "[INFO] Resetting project items..."
  gh project item-list "$NUMBER" --owner "$OWNER" --format=json > project_items_backup.json
  jq -r '.items[].id' project_items_backup.json | grep -v '^\s*$' | \
    xargs -I{} gh project item-delete "$NUMBER" --owner "$OWNER" --id {}
  echo "[INFO] All project items deleted. Backup saved to project_items_backup.json"

fi

# ==== CSV Import (Epic,Story,Task,Priority,Due Date) ====
: "${OWNER:?ENV OWNER is required}"
: "${NUMBER:?ENV NUMBER is required}"
: "${CSV_FILE:?ENV CSV_FILE is required}"

if [[ ! -f "$CSV_FILE" ]]; then
  echo "[ERROR] CSV_FILE not found: $CSV_FILE" >&2
  exit 1
fi

# Resolve project and field metadata once
PROJECT_JSON=$(gh project view "$NUMBER" --owner "$OWNER" --format=json)
PROJECT_ID=$(echo "$PROJECT_JSON" | jq -r '.id')
if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "null" ]]; then
  echo "[ERROR] Failed to resolve project ID for $OWNER/$NUMBER" >&2
  exit 1
fi

# Ensure required fields exist (idempotent)
# Title はデフォルト内蔵。ここでは Epic(Text) / Story(Text) / Priority(SingleSelect) / Due Date(Date) を作成
create_field_if_missing() {
  local NAME="$1"; shift
  local TYPE="$1"; shift
  local EXTRA_ARGS=("$@")
  if ! gh project field-list "$NUMBER" --owner "$OWNER" --format=json | jq -e --arg n "$NAME" '.fields[] | select(.name==$n)' >/dev/null; then
    echo "[INFO] Creating field '$NAME' ($TYPE)"
    gh project field-create "$NUMBER" --owner "$OWNER" --name "$NAME" --data-type "$TYPE" "${EXTRA_ARGS[@]}" >/dev/null
  else
    echo "[INFO] Field '$NAME' already exists. Skipping create."
  fi
}

# Priority はオプション付きで作成（High,Medium,Low）
create_field_if_missing "Epic" "TEXT"
create_field_if_missing "Story" "TEXT"
create_field_if_missing "Due Date" "DATE"
create_field_if_missing "Priority" "SINGLE_SELECT" --single-select-options "High,Medium,Low"

FIELDS_JSON=$(gh project field-list "$NUMBER" --owner "$OWNER" --format=json)

EPIC_FIELD_ID=$(echo "$FIELDS_JSON" | jq -r '.fields[] | select(.name=="Epic") | .id')
STORY_FIELD_ID=$(echo "$FIELDS_JSON" | jq -r '.fields[] | select(.name=="Story") | .id')
PRIORITY_FIELD_ID=$(echo "$FIELDS_JSON" | jq -r '.fields[] | select(.name=="Priority") | .id')
DUE_FIELD_ID=$(echo "$FIELDS_JSON" | jq -r '.fields[] | select(.name=="Due Date") | .id')

PRIORITY_HIGH_ID=$(echo "$FIELDS_JSON" | jq -r '.fields[] | select(.name=="Priority") | .options[] | select(.name=="High") | .id')
PRIORITY_MEDIUM_ID=$(echo "$FIELDS_JSON" | jq -r '.fields[] | select(.name=="Priority") | .options[] | select(.name=="Medium") | .id')
PRIORITY_LOW_ID=$(echo "$FIELDS_JSON" | jq -r '.fields[] | select(.name=="Priority") | .options[] | select(.name=="Low") | .id')

# Sanity log
echo "[INFO] Project ID: $PROJECT_ID"
echo "[INFO] Field IDs - Epic:$EPIC_FIELD_ID Story:$STORY_FIELD_ID Priority:$PRIORITY_FIELD_ID Due:$DUE_FIELD_ID"
echo "[INFO] Note: Fields exist at the project level. If you don't see 'Epic/Story/Priority/Due Date' as columns in the current view, click the '+' in the header to add them to the view."

# Helper: remove surrounding double quotes if present
strip_outer_quotes() {
  local s="$1"
  # Remove leading and trailing CR, then outer quotes
  s="${s%$'\r'}"
  s="${s#$'\r'}"
  if [[ "$s" == '"'*'"' ]]; then
    s="${s#"\""}"
    s="${s%"\""}"
  fi
  printf '%s' "$s"
}

echo "[INFO] Starting CSV import from $CSV_FILE"
# Skip header and iterate rows
# Expect columns: Epic,Story,Task,Priority,Due Date
# Note: This simple parser assumes fields do not contain embedded commas.
# If your data may include commas, consider switching to a Python CSV reader.

tail -n +2 "$CSV_FILE" | while IFS=, read -r EPIC STORY TASK PRIORITY DUE_DATE; do
  # Trim whitespace and remove outer quotes
  EPIC=$(strip_outer_quotes "$EPIC")
  STORY=$(strip_outer_quotes "$STORY")
  TASK=$(strip_outer_quotes "$TASK")
  PRIORITY=$(strip_outer_quotes "$PRIORITY")
  DUE_DATE=$(strip_outer_quotes "$DUE_DATE")

  # Skip blank lines
  if [[ -z "$EPIC$STORY$TASK$PRIORITY$DUE_DATE" ]]; then
    continue
  fi

  if [[ -z "$TASK" ]]; then
    echo "[WARN] Skipping row with empty Task: Epic=$EPIC Story=$STORY" >&2
    continue
  fi

  echo "[INFO] Creating item: $TASK"
  ITEM_JSON=$(gh project item-create "$NUMBER" --owner "$OWNER" --title "$TASK" --format=json)
  ITEM_ID=$(echo "$ITEM_JSON" | jq -r '.id')

  if [[ -z "$ITEM_ID" || "$ITEM_ID" == "null" ]]; then
    echo "[ERROR] Failed to create item for Task=$TASK" >&2
    continue
  fi

  # --- Set fields using new CLI syntax (one field per call) ---
  if [[ -n "$EPIC" && -n "$EPIC_FIELD_ID" && "$EPIC_FIELD_ID" != "null" ]]; then
    gh project item-edit --project-id "$PROJECT_ID" --id "$ITEM_ID" --field-id "$EPIC_FIELD_ID" --text "$EPIC"
  fi

  if [[ -n "$STORY" && -n "$STORY_FIELD_ID" && "$STORY_FIELD_ID" != "null" ]]; then
    gh project item-edit --project-id "$PROJECT_ID" --id "$ITEM_ID" --field-id "$STORY_FIELD_ID" --text "$STORY"
  fi

  if [[ -n "$DUE_DATE" && -n "$DUE_FIELD_ID" && "$DUE_FIELD_ID" != "null" ]]; then
    gh project item-edit --project-id "$PROJECT_ID" --id "$ITEM_ID" --field-id "$DUE_FIELD_ID" --date "$DUE_DATE"
  fi

  if [[ -n "$PRIORITY" && -n "$PRIORITY_FIELD_ID" && "$PRIORITY_FIELD_ID" != "null" ]]; then
    case "$PRIORITY" in
      High)
        OPT_ID="$PRIORITY_HIGH_ID";;
      Medium)
        OPT_ID="$PRIORITY_MEDIUM_ID";;
      Low)
        OPT_ID="$PRIORITY_LOW_ID";;
      *)
        OPT_ID="";;
    esac
    if [[ -n "$OPT_ID" && "$OPT_ID" != "null" ]]; then
      gh project item-edit --project-id "$PROJECT_ID" --id "$ITEM_ID" --field-id "$PRIORITY_FIELD_ID" --single-select-option-id "$OPT_ID"
    else
      echo "[WARN] Unknown Priority '$PRIORITY' for Task=$TASK (skipped)" >&2
    fi
  fi

done

echo "[INFO] CSV import finished"
