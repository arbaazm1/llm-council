# Prompt Template Library

The LLM Council now includes a collapsible right-side panel that serves as a prompt template library. This feature allows you to create, edit, and manage reusable prompt templates with dynamic fields.

## Features

### 1. **Collapsible Panel**
- Click the arrow button (◀/▶) in the header to collapse/expand the panel
- When collapsed, the panel takes minimal space to maximize chat area
- When expanded, provides full access to template management

### 2. **Creating Templates**
- Click the "+ New Template" button to create a new template
- Fill in the template name (optional - auto-generated if left empty)
- Write your prompt in the body field
- Use `{{field_name}}` syntax to define dynamic fields/parameters
- Example: `Write a {{content_type}} about {{topic}} in a {{tone}} tone.`

#### Field Detection
The system automatically detects fields in your template:
- Fields must follow the `{{field_name}}` format
- Field names can only contain letters, numbers, and underscores
- Detected fields are displayed below the template body
- Fields are extracted in order of appearance (duplicates removed)

### 3. **Using Templates**
- Click on any template in the list to open it in view mode
- The full prompt template is displayed with a live preview
- Each detected field gets its own text input box
- As you type in the parameter fields, the preview updates in real-time
- The preview shows your prompt with all parameters filled in
- Unfilled parameters remain as `{{field_name}}` in the preview

### 4. **Editing Templates**
- From the view mode, click the ✏️ (pencil) icon to edit
- Or access the template editor from the template view
- The same form as creation appears with pre-filled data
- Modify the name and/or body as needed
- Click "Update" to save changes or "Cancel" to discard

### 5. **Deleting Templates**
- Click the 🗑️ (trash) icon on any template from the list view
- A confirmation dialog will appear
- Confirm to permanently delete the template

### 6. **Template List View**
Each template in the list shows:
- **Template Name**: The title of the template
- **Field Count**: Number of detected fields (e.g., "3 fields" or "No fields")
- Templates are sorted by creation date (newest first)

## Example Templates

### Basic Content Generation
```
Write a {{content_type}} about {{topic}} in a {{tone}} tone.

Key points to cover:
- {{point1}}
- {{point2}}
- {{point3}}

Target audience: {{audience}}
```
**Fields**: content_type, topic, tone, point1, point2, point3, audience

### Code Review Request
```
Please review the following {{language}} code:

{{code}}

Focus on:
- Code quality
- Best practices
- Potential bugs
- {{specific_concern}}
```
**Fields**: language, code, specific_concern

### Email Template
```
Write a {{formality}} email to {{recipient}} about {{subject}}.

Context: {{context}}

Key points to include:
{{key_points}}

Desired action: {{call_to_action}}
```
**Fields**: formality, recipient, subject, context, key_points, call_to_action

## Technical Details

### Storage
- Templates are stored in `data/templates/` directory
- Each template is a JSON file with UUID as filename
- Templates include: id, name, body, fields, created_at, updated_at

### Auto-Generated Names
If no name is provided:
- The system uses the first line of the template body
- Truncated to 50 characters if longer
- Defaults to "Untitled Template" if body is empty

### API Endpoints
- `GET /api/templates` - List all templates
- `POST /api/templates` - Create a new template
- `GET /api/templates/{id}` - Get a specific template
- `PUT /api/templates/{id}` - Update a template
- `DELETE /api/templates/{id}` - Delete a template

## Using Templates in Your Workflow

1. **Create** your templates once with clear parameter fields
2. **Click** on a template to open it in view mode
3. **Fill in** the parameter values for your specific use case
4. **Watch** the live preview update as you type
5. **Copy** the completed prompt from the preview to use in your conversation

## Best Practices

1. **Use Descriptive Names**: Give templates clear, descriptive names
2. **Consistent Field Naming**: Use snake_case for field names (e.g., `{{user_name}}`)
3. **Document Fields**: Consider adding comments in your template body explaining what each field expects
4. **Keep It Modular**: Create focused templates for specific tasks rather than all-in-one templates
5. **Version Control**: Consider backing up your templates directory for important templates
6. **Test Your Templates**: After creating a template, view it immediately to ensure fields are detected correctly

## UI Flow

```
List View → Click Template → View Mode (with live preview)
                                ↓
                        ← Back | Edit ✏️ →
                                ↓
                         Edit Mode → Save
```

## Future Enhancements

Potential features for future versions:
- Template categories/tags
- Search and filter functionality
- Template sharing/export
- Template usage statistics
- One-click copy to clipboard from preview
- Direct template application to chat input
- Template variables with default values
- Template validation and testing

