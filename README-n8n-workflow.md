# N8N Telegram Expense Bot Integration

## Overview

This n8n workflow integrates a Telegram bot with a Django expense management system, allowing users to register expenses via text or audio messages using natural language processing powered by OpenAI.

## Features

- **Multi-modal Input**: Supports both text and audio messages
- **Natural Language Processing**: Uses OpenAI GPT-4 for expense extraction
- **User Authorization**: Validates users via Django API
- **Conversation State Management**: Handles follow-up questions for incomplete data
- **Credit Card Support**: Manages installment payments
- **Error Handling**: Comprehensive error handling and user feedback
- **Real-time Responses**: Immediate feedback via Telegram

## Architecture

### Workflow Components

1. **Telegram Webhook Trigger**: Receives messages from Telegram
2. **User Authorization Check**: Validates user via Django API
3. **Message Type Detection**: Determines if message is text or audio
4. **Audio Processing**: Downloads and transcribes audio using OpenAI Whisper
5. **OpenAI Analysis**: Extracts expense data using GPT-4
6. **Conditional Logic**: Handles complete vs incomplete expense data
7. **Django API Integration**: Creates expenses in Django backend
8. **Response Formatting**: Sends formatted responses back to Telegram
9. **Conversation State Management**: Manages multi-turn conversations

### Data Flow

```
Telegram Message → User Validation → Message Processing → OpenAI Analysis → Django API → Telegram Response
```

## Prerequisites

- n8n instance (v1.0+)
- Telegram Bot Token
- OpenAI API Key
- Django backend with expense management API
- HTTPS endpoint for Telegram webhooks

## Installation & Setup

### 1. Environment Setup

Create a `.env` file or set environment variables:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Django API Configuration
DJANGO_API_BASE_URL=https://your-django-api.com
DJANGO_API_TOKEN=your_django_api_token

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# n8n Configuration
N8N_WEBHOOK_URL=https://your-n8n-instance.com
```

### 2. Import Workflow

1. Open n8n dashboard
2. Go to Workflows → Import from File
3. Upload `n8n-telegram-expense-workflow.json`
4. Upload `n8n-conversation-state-workflow.json`

### 3. Configure Credentials

Set up the following credentials in n8n:

#### OpenAI API
- **Name**: `OpenAI API`
- **API Key**: Your OpenAI API key

#### Telegram Bot Token
Configure in the Telegram Webhook Trigger node:
- **Bot Token**: Your Telegram bot token

#### Django API Token
Configure in HTTP Request nodes:
- **Authorization Header**: `Bearer your_django_api_token`

### 4. Update API URLs

Update the following URLs in the workflow nodes:

- **User Authorization Check**: `https://your-django-api.com/accounts/verify_user_by_telegram_chat_id/`
- **Expense Creation**: `https://your-django-api.com/api/expenses/`
- **Conversation State**: `http://localhost:5678/webhook/conversation-state`

### 5. Telegram Bot Setup

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Set webhook URL:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
        -d "url=https://your-n8n-instance.com/webhook/telegram-webhook"
   ```

## Configuration Details

### OpenAI Prompts

The workflow uses specific prompts for expense extraction. Key categories and payment methods are predefined:

**Categories**: Comida, Transporte, Entretenimiento, Salud, Educación, Servicios, Otros

**Payment Methods**:
- efectivo: efectivo
- debito: mercado_pago, visa_frances, visa_bapro, visa_macro, cuenta_dni
- transferencia: transferencia_mp, transferencia_frances, transferencia_macro, transferencia_bapro, transferencia_cuenta_dni
- credito: mastercard_frances, visa_frances_credito, visa_bapro_credito, mercado_pago_credito

### Conversation State Management

The workflow maintains conversation state for follow-up questions:

- **State Storage**: Uses n8n's workflow data storage
- **State Key**: `{chatId}_conversation_state`
- **State Data**: JSON object containing incomplete expense data and original message

### Error Handling

The workflow handles various error scenarios:

- **Unauthorized Users**: Returns access denied message
- **API Failures**: Logs errors and sends user-friendly messages
- **Incomplete Data**: Prompts user for missing information
- **Invalid Data**: Validates data before API calls

## Testing

### Test Cases

Use the provided `test-data.json` file containing sample test cases:

1. **Complete expense text message**
2. **Incomplete expense text message**
3. **Audio message processing**
4. **Unauthorized user handling**
5. **Credit expense with installments**
6. **Follow-up message handling**

### Manual Testing

1. Send a message to your Telegram bot
2. Check n8n workflow execution logs
3. Verify expense creation in Django admin
4. Confirm Telegram response

### Automated Testing

```bash
# Test with sample data
curl -X POST "https://your-n8n-instance.com/webhook/telegram-webhook" \
     -H "Content-Type: application/json" \
     -d @test-data.json
```

## Monitoring & Troubleshooting

### Logs

Monitor workflow execution in n8n dashboard:
- **Workflow Executions**: View execution history
- **Node Logs**: Check individual node outputs
- **Error Logs**: Identify and debug failures

### Common Issues

#### 1. Telegram Webhook Not Receiving Messages

**Symptoms**: Bot doesn't respond to messages
**Solution**:
- Verify webhook URL is set correctly
- Check HTTPS certificate validity
- Ensure n8n instance is publicly accessible

#### 2. OpenAI API Errors

**Symptoms**: Transcription or analysis fails
**Solution**:
- Verify API key is valid and has sufficient credits
- Check API rate limits
- Ensure correct model names (whisper-1, gpt-4)

#### 3. Django API Connection Issues

**Symptoms**: Expense creation fails
**Solution**:
- Verify API endpoints are accessible
- Check authentication token validity
- Ensure CORS is properly configured

#### 4. Conversation State Not Working

**Symptoms**: Follow-up messages not recognized
**Solution**:
- Verify conversation state workflow is active
- Check webhook URLs are correct
- Ensure workflow data storage is enabled

### Performance Optimization

1. **Caching**: Implement caching for user validation
2. **Rate Limiting**: Add rate limiting for API calls
3. **Batch Processing**: Group multiple messages if needed
4. **Error Retry**: Implement retry logic for failed API calls

## Security Considerations

1. **API Keys**: Store securely using n8n credentials
2. **HTTPS**: Ensure all webhooks use HTTPS
3. **Input Validation**: Validate all user inputs
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Audit Logging**: Log all expense creation activities

## Deployment

### Production Deployment

1. **Environment Variables**: Use secure environment variables
2. **Monitoring**: Set up monitoring and alerts
3. **Backup**: Regular workflow backups
4. **Scaling**: Consider load balancing for high traffic

### Docker Deployment

```yaml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your_secure_password
    volumes:
      - ./n8n-data:/home/node/.n8n
    ports:
      - "5678:5678"
```

## API Reference

### Telegram Webhook Payload

```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 123,
    "from": {
      "id": 123456789,
      "username": "testuser"
    },
    "chat": {
      "id": 123456789,
      "type": "private"
    },
    "date": 1640995200,
    "text": "Gasté $1500 en comida"
  }
}
```

### Django API Endpoints

- **User Verification**: `GET /accounts/verify_user_by_telegram_chat_id/?telegram_chat_id={id}`
- **Expense Creation**: `POST /api/expenses/`

### Conversation State API

- **Get State**: `POST /webhook/conversation-state` with `{"action": "get", "chatId": "123"}`
- **Update State**: `POST /webhook/conversation-state` with `{"action": "update", "chatId": "123", "newStateData": {...}}`
- **Clear State**: `POST /webhook/conversation-state` with `{"action": "clear", "chatId": "123"}`

## Support

For issues and questions:
1. Check n8n workflow execution logs
2. Verify all credentials and URLs
3. Test individual nodes manually
4. Review error messages and responses

## Version History

- **v1.0**: Initial implementation with basic expense registration
- **v1.1**: Added conversation state management
- **v1.2**: Enhanced error handling and audio support
- **v1.3**: Added credit card installment support