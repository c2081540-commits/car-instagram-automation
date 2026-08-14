const CONFIG = {
  spreadsheetId: PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID'),
  sheetName: PropertiesService.getScriptProperties().getProperty('SHEET_NAME') || 'control',
  switchCell: PropertiesService.getScriptProperties().getProperty('SWITCH_CELL') || 'B1',
  githubOwner: PropertiesService.getScriptProperties().getProperty('GITHUB_OWNER') || 'c2081540-commits',
  githubRepo: PropertiesService.getScriptProperties().getProperty('GITHUB_REPO') || 'car-instagram-automation',
  githubWorkflow: PropertiesService.getScriptProperties().getProperty('GITHUB_WORKFLOW') || 'publish_due.yml',
  githubRef: PropertiesService.getScriptProperties().getProperty('GITHUB_REF') || 'main',
  githubToken: PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN')
};

function dispatchInstagramPublisher() {
  validateConfig_();

  const sheet = SpreadsheetApp.openById(CONFIG.spreadsheetId).getSheetByName(CONFIG.sheetName);
  if (!sheet) {
    throw new Error('Control sheet not found: ' + CONFIG.sheetName);
  }

  const enabled = String(sheet.getRange(CONFIG.switchCell).getDisplayValue()).trim();
  if (enabled !== '1') {
    console.log('Instagram auto publish is OFF. No workflow dispatched.');
    return;
  }

  // GAS intentionally does not inspect queue.json, scheduled_at, due windows, or late status.
  // Python in publish.py/post_queue.py is the single source of truth for reservation logic.
  const url = [
    'https://api.github.com/repos',
    encodeURIComponent(CONFIG.githubOwner),
    encodeURIComponent(CONFIG.githubRepo),
    'actions/workflows',
    encodeURIComponent(CONFIG.githubWorkflow),
    'dispatches'
  ].join('/');

  const response = UrlFetchApp.fetch(url, {
    method: 'post',
    muteHttpExceptions: true,
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + CONFIG.githubToken,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28'
    },
    payload: JSON.stringify({ ref: CONFIG.githubRef })
  });

  const code = response.getResponseCode();
  if (code !== 204) {
    throw new Error('GitHub workflow dispatch failed: HTTP ' + code + ' ' + response.getContentText());
  }

  console.log('Publish Due Story workflow dispatched. Python will decide whether anything is due.');
}

function validateConfig_() {
  const required = {
    SPREADSHEET_ID: CONFIG.spreadsheetId,
    GITHUB_TOKEN: CONFIG.githubToken
  };
  const missing = Object.keys(required).filter(function(key) { return !required[key]; });
  if (missing.length) {
    throw new Error('Missing GAS Script Properties: ' + missing.join(', '));
  }
}
