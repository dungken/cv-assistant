const fs = require('fs');
const file = '/home/dungken/Desktop/Workspace/utc2/cv_assistant/frontend/src/components/features/CVUpload.tsx';
let content = fs.readFileSync(file, 'utf-8');

// Insert performAutoSave function
const autoSaveFunc = `
  const performAutoSave = async (latestResult: ParseResult) => {
    if (!docIdParam) return;
    try {
      await cvDocumentApi.createVersion(parseInt(docIdParam), {
        dataJson: JSON.stringify(latestResult),
        note: 'Auto-saved from section edit'
      });
      // Silently update history list
      loadSavedParses();
      setSaveSuccess(true);
    } catch (e) {
      console.error('Auto-save failed:', e);
    }
  };
`;

content = content.replace('const handleUpdateItem = ', autoSaveFunc + '\n  const handleUpdateItem = ');

// Add performAutoSave to all edit handlers
content = content.replace(/onParsedCvData\?\.\(mapParseResultToCvData\(newResult\)\);\s*};/g, 'onParsedCvData?.(mapParseResultToCvData(newResult));\n    performAutoSave(newResult);\n  };');

fs.writeFileSync(file, content);
