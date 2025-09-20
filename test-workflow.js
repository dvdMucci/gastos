#!/usr/bin/env node

/**
 * N8N Telegram Expense Bot Workflow Test Script
 *
 * This script simulates Telegram webhook payloads and tests the workflow logic
 * without requiring actual n8n deployment.
 */

const fs = require('fs');
const path = require('path');

// Load test data
const testDataPath = path.join(__dirname, 'test-data.json');
const testData = JSON.parse(fs.readFileSync(testDataPath, 'utf8'));

/**
 * Mock n8n node execution
 */
class MockNode {
  constructor(name, config) {
    this.name = name;
    this.config = config;
    this.output = null;
  }

  execute(input) {
    console.log(`\n📍 Executing node: ${this.name}`);
    console.log(`📥 Input:`, JSON.stringify(input, null, 2));

    // Simulate node execution based on type
    switch (this.config.type) {
      case 'webhook':
        this.output = this.mockWebhook(input);
        break;
      case 'httpRequest':
        this.output = this.mockHttpRequest(input);
        break;
      case 'set':
        this.output = this.mockSetNode(input);
        break;
      case 'if':
        this.output = this.mockIfNode(input);
        break;
      case 'openai':
        this.output = this.mockOpenAI(input);
        break;
      default:
        this.output = input;
    }

    console.log(`📤 Output:`, JSON.stringify(this.output, null, 2));
    return this.output;
  }

  mockWebhook(input) {
    // Return the webhook payload as-is
    return input;
  }

  mockHttpRequest(input) {
    const url = this.config.url || '';
    const method = this.config.method || 'GET';

    console.log(`🌐 HTTP ${method} ${url}`);

    // Mock responses based on URL patterns
    if (url.includes('verify_user_by_telegram_chat_id')) {
      const chatId = input.body?.message?.from?.id;
      if (chatId === 123456789) {
        return testData.mock_responses.django_user_check_authorized;
      } else {
        return testData.mock_responses.django_user_check_unauthorized;
      }
    }

    if (url.includes('api.telegram.org/bot')) {
      if (url.includes('getFile')) {
        return testData.mock_responses.telegram_get_file;
      }
      if (url.includes('sendMessage')) {
        return { ok: true, result: { message_id: 123 } };
      }
    }

    if (url.includes('api/expenses')) {
      return testData.mock_responses.django_expense_creation;
    }

    return { statusCode: 200, body: { success: true } };
  }

  mockSetNode(input) {
    const values = this.config.values || {};
    const result = { ...input };

    // Apply value transformations
    if (values.string) {
      values.string.forEach(item => {
        let value = item.value;

        // Replace expressions with mock data
        if (value.includes('$json.body.message')) {
          value = value.replace(/\{\{.*?\}\}/g, (match) => {
            if (match.includes('voice')) return 'true';
            if (match.includes('text')) return input.body?.message?.text || '';
            if (match.includes('chat.id')) return input.body?.message?.chat?.id || '';
            return '';
          });
        }

        result[item.name] = value;
      });
    }

    return result;
  }

  mockIfNode(input) {
    const conditions = this.config.conditions || {};

    if (conditions.boolean) {
      const condition = conditions.boolean[0];
      let value1 = condition.value1;
      let value2 = condition.value2;

      // Evaluate condition
      if (value1.includes('$json.statusCode')) {
        value1 = input.statusCode;
      }
      if (value1.includes('$json.complete')) {
        value1 = input.complete;
      }

      const result = eval(`${value1} ${condition.operation === 'equal' ? '===' : '!=='} ${value2}`);
      console.log(`🔀 Condition: ${value1} ${condition.operation} ${value2} = ${result}`);

      return result;
    }

    return false;
  }

  mockOpenAI(input) {
    const model = this.config.model;

    if (model === 'whisper-1') {
      return testData.mock_responses.openai_transcription;
    }

    if (model === 'gpt-4') {
      // Check if the input text is complete or incomplete
      const text = input.finalText || '';
      if (text.includes('Compré algo por $500')) {
        return testData.mock_responses.openai_analysis_incomplete;
      } else {
        return testData.mock_responses.openai_analysis_complete;
      }
    }

    return { text: 'Mock response' };
  }
}

/**
 * Simulate workflow execution
 */
function simulateWorkflow(testCase) {
  console.log(`\n🚀 Testing: ${testCase.name}`);
  console.log(`📝 Description: ${testCase.description}`);

  // Create mock nodes (simplified version of the actual workflow)
  const nodes = [
    new MockNode('Telegram Webhook', { type: 'webhook' }),
    new MockNode('User Authorization Check', {
      type: 'httpRequest',
      method: 'GET',
      url: 'verify_user_by_telegram_chat_id'
    }),
    new MockNode('User Authorized?', {
      type: 'if',
      conditions: {
        boolean: [{ value1: '$json.statusCode', operation: 'equal', value2: '200' }]
      }
    }),
    new MockNode('Message Type Detection', {
      type: 'set',
      values: {
        string: [
          { name: 'messageType', value: '{{ $json.body.message?.voice ? "audio" : "text" }}' },
          { name: 'messageText', value: '{{ $json.body.message?.text || "" }}' },
          { name: 'chatId', value: '{{ $json.body.message?.chat?.id }}' }
        ]
      }
    }),
    new MockNode('Merge Text Sources', {
      type: 'set',
      values: {
        string: [
          { name: 'finalText', value: '{{ $node["message-type-detection"].json.messageText }}' }
        ]
      }
    }),
    new MockNode('OpenAI Expense Analysis', {
      type: 'openai',
      model: 'gpt-4'
    }),
    new MockNode('Expense Data Complete?', {
      type: 'if',
      conditions: {
        boolean: [{ value1: '$json.complete', operation: 'true' }]
      }
    })
  ];

  // Execute workflow
  let currentData = testCase.input;

  try {
    for (const node of nodes) {
      currentData = node.execute(currentData);

      // Handle conditional branching
      if (node.name === 'User Authorized?' && !currentData) {
        console.log('❌ User not authorized - stopping workflow');
        break;
      }

      if (node.name === 'Expense Data Complete?' && !currentData) {
        console.log('⚠️ Expense data incomplete - would trigger follow-up');
        break;
      }
    }

    console.log(`\n✅ Test completed successfully`);

  } catch (error) {
    console.error(`❌ Test failed:`, error.message);
  }
}

/**
 * Run all tests
 */
function runAllTests() {
  console.log('🧪 Starting N8N Workflow Tests\n');
  console.log('=' .repeat(50));

  testData.test_cases.forEach((testCase, index) => {
    console.log(`\n${index + 1}. ${testCase.name}`);
    console.log('-'.repeat(30));
    simulateWorkflow(testCase);
  });

  console.log('\n' + '='.repeat(50));
  console.log('🏁 All tests completed');
}

/**
 * Run specific test
 */
function runTest(testName) {
  const testCase = testData.test_cases.find(tc => tc.name === testName);
  if (testCase) {
    simulateWorkflow(testCase);
  } else {
    console.error(`❌ Test case "${testName}" not found`);
    console.log('Available tests:');
    testData.test_cases.forEach(tc => console.log(`  - ${tc.name}`));
  }
}

// CLI interface
const args = process.argv.slice(2);

if (args.length === 0) {
  runAllTests();
} else if (args[0] === '--test') {
  runTest(args[1]);
} else {
  console.log('Usage:');
  console.log('  node test-workflow.js              # Run all tests');
  console.log('  node test-workflow.js --test "Test Name"  # Run specific test');
  console.log('\nAvailable tests:');
  testData.test_cases.forEach(tc => console.log(`  - ${tc.name}`));
}

module.exports = { simulateWorkflow, MockNode };