import { useState, useEffect, useMemo } from 'react';
import './PromptTemplateLibrary.css';

const EXAMPLE_TEMPLATE = `Write a {{content_type}} about {{topic}} in a {{tone}} tone.

Key points to cover:
- {{point1}}
- {{point2}}
- {{point3}}

Target audience: {{audience}}`;

export default function PromptTemplateLibrary({
  templates,
  onCreateTemplate,
  onUpdateTemplate,
  onDeleteTemplate,
  onRefreshTemplates,
  onUseTemplate,
  isOpen,
  onClose,
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mode, setMode] = useState('list'); // 'list', 'view', 'edit', 'create'
  const [currentTemplate, setCurrentTemplate] = useState(null);
  const [formData, setFormData] = useState({ name: '', body: '' });
  const [parameterValues, setParameterValues] = useState({});

  useEffect(() => {
    onRefreshTemplates();
  }, []);

  const handleNewTemplate = () => {
    setCurrentTemplate(null);
    setFormData({ name: '', body: EXAMPLE_TEMPLATE });
    setMode('create');
  };

  const handleViewTemplate = (template) => {
    setCurrentTemplate(template);
    // Initialize parameter values to empty strings
    const initialValues = {};
    template.fields.forEach((field) => {
      initialValues[field] = '';
    });
    setParameterValues(initialValues);
    setMode('view');
  };

  const handleEditTemplate = (template) => {
    setCurrentTemplate(template);
    setFormData({ name: template.name, body: template.body });
    setMode('edit');
  };

  const handleDeleteTemplate = (e, template) => {
    e.stopPropagation();
    const confirmed = window.confirm(
      `Are you sure you want to delete "${template.name}"?`
    );
    if (confirmed) {
      onDeleteTemplate(template.id);
    }
  };

  const handleEditClick = (e, template) => {
    e.stopPropagation();
    handleEditTemplate(template);
  };

  const handleSaveTemplate = async () => {
    if (mode === 'edit') {
      // Update existing template
      await onUpdateTemplate(currentTemplate.id, formData.name, formData.body);
    } else {
      // Create new template
      await onCreateTemplate(formData.name, formData.body);
    }
    setMode('list');
    setCurrentTemplate(null);
    setFormData({ name: '', body: '' });
  };

  const handleCancel = () => {
    setMode('list');
    setCurrentTemplate(null);
    setFormData({ name: '', body: '' });
    setParameterValues({});
  };

  const handleBackToList = () => {
    setMode('list');
    setCurrentTemplate(null);
    setParameterValues({});
  };

  const extractFields = (body) => {
    const pattern = /\{\{(\w+)\}\}/g;
    const matches = [...body.matchAll(pattern)];
    const fields = [...new Set(matches.map((match) => match[1]))];
    return fields;
  };

  const renderPromptWithValues = (body, values) => {
    let result = body;
    Object.keys(values).forEach((field) => {
      // Only replace if there's a value, otherwise keep the placeholder
      const value = values[field];
      if (value && value.trim() !== '') {
        const pattern = new RegExp(`\\{\\{${field}\\}\\}`, 'g');
        result = result.replace(pattern, value);
      }
    });
    return result;
  };

  // Memoize the rendered prompt to ensure it updates when parameters change
  const renderedPrompt = useMemo(() => {
    if (mode === 'view' && currentTemplate) {
      return renderPromptWithValues(currentTemplate.body, parameterValues);
    }
    return '';
  }, [mode, currentTemplate, parameterValues]);

  // Check if all parameters are filled
  const allParametersFilled = useMemo(() => {
    if (mode === 'view' && currentTemplate) {
      return currentTemplate.fields.every(
        (field) => parameterValues[field] && parameterValues[field].trim() !== ''
      );
    }
    return false;
  }, [mode, currentTemplate, parameterValues]);

  const handleUseTemplateClick = () => {
    if (allParametersFilled && onUseTemplate) {
      onUseTemplate(renderedPrompt);
    }
  };

  return (
    <div className={`template-library ${isCollapsed ? 'collapsed' : ''} ${isOpen ? 'open' : ''}`}>
      <div className="template-library-header">
        {!isCollapsed && (
          <>
            <h2>Prompt Templates</h2>
            {mode === 'list' && (
              <button className="new-template-btn" onClick={handleNewTemplate}>
                + New Template
              </button>
            )}
          </>
        )}
        <button
          className="collapse-toggle"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? 'Expand panel' : 'Collapse panel'}
        >
          {isCollapsed ? '⋮' : '×'}
        </button>
      </div>

      {!isCollapsed && (
        <>
          {mode === 'view' ? (
            <div className="template-viewer">
              <div className="viewer-header">
                <button className="back-btn" onClick={handleBackToList}>
                  ← Back
                </button>
                <h3>{currentTemplate.name}</h3>
              </div>
              <div className="viewer-content">
                <div className="preview-section">
                  <div className="prompt-preview">
                    {renderedPrompt}
                  </div>
                </div>
                {currentTemplate.fields.length > 0 ? (
                  <div className="parameters-section">
                    <h4>Parameters</h4>
                    <div className="parameter-inputs">
                      {currentTemplate.fields.map((field) => (
                        <div key={field} className="parameter-input-group">
                          <label htmlFor={`param-${field}`}>{field}</label>
                          <input
                            id={`param-${field}`}
                            type="text"
                            placeholder={`Enter ${field}...`}
                            value={parameterValues[field] || ''}
                            onChange={(e) =>
                              setParameterValues({
                                ...parameterValues,
                                [field]: e.target.value,
                              })
                            }
                          />
                        </div>
                      ))}
                    </div>
                    <button
                      className={`use-template-btn ${
                        allParametersFilled ? 'enabled' : 'disabled'
                      }`}
                      onClick={handleUseTemplateClick}
                      disabled={!allParametersFilled}
                    >
                      Use Template
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="no-parameters">
                      This template has no parameters
                    </div>
                    <button
                      className="use-template-btn enabled"
                      onClick={handleUseTemplateClick}
                    >
                      Use Template
                    </button>
                  </>
                )}
              </div>
            </div>
          ) : mode === 'edit' || mode === 'create' ? (
            <div className="template-editor">
              <div className="editor-header">
                <h3>{mode === 'edit' ? 'Edit Template' : 'New Template'}</h3>
              </div>
              <div className="editor-form">
                <div className="form-group">
                  <label htmlFor="template-name">Name</label>
                  <input
                    id="template-name"
                    type="text"
                    className="template-name-input"
                    placeholder="Template name (leave empty for auto-generation)"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="template-body">
                    Template Body
                    <span className="field-hint">
                      Use {`{{field_name}}`} for fields/parameters
                    </span>
                  </label>
                  <textarea
                    id="template-body"
                    className="template-body-input"
                    placeholder="Enter your template here..."
                    value={formData.body}
                    onChange={(e) =>
                      setFormData({ ...formData, body: e.target.value })
                    }
                    rows={12}
                  />
                </div>
                {formData.body && (
                  <div className="detected-fields">
                    <strong>Detected fields:</strong>{' '}
                    {extractFields(formData.body).length > 0 ? (
                      <span className="fields-list">
                        {extractFields(formData.body).map((field, index) => (
                          <span key={field} className="field-tag">
                            {field}
                            {index < extractFields(formData.body).length - 1
                              ? ', '
                              : ''}
                          </span>
                        ))}
                      </span>
                    ) : (
                      <span className="no-fields">None</span>
                    )}
                  </div>
                )}
                <div className="editor-actions">
                  <button className="save-btn" onClick={handleSaveTemplate}>
                    {mode === 'edit' ? 'Update' : 'Create'}
                  </button>
                  <button className="cancel-btn" onClick={handleCancel}>
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          ) : mode === 'list' ? (
            <div className="template-list">
              {templates.length === 0 ? (
                <div className="no-templates">No templates yet</div>
              ) : (
                templates.map((template) => (
                  <div
                    key={template.id}
                    className="template-item"
                    onClick={() => handleViewTemplate(template)}
                  >
                    <div className="template-content">
                      <div className="template-name">{template.name}</div>
                      <div className="template-meta">
                        {template.fields.length > 0 ? (
                          <span className="fields-count">
                            {template.fields.length} field
                            {template.fields.length !== 1 ? 's' : ''}
                          </span>
                        ) : (
                          <span className="fields-count">No fields</span>
                        )}
                      </div>
                    </div>
                    <div className="template-actions">
                      <button
                        className="edit-template-btn"
                        onClick={(e) => handleEditClick(e, template)}
                        title="Edit template"
                        aria-label="Edit template"
                      >
                        ✏️
                      </button>
                      <button
                        className="delete-template-btn"
                        onClick={(e) => handleDeleteTemplate(e, template)}
                        title="Delete template"
                        aria-label="Delete template"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

