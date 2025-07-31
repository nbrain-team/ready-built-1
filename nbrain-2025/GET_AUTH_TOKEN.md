# How to Get Your Auth Token

To run the calendar sync debug script, you need your authentication token.

## Steps:

1. **Open your browser** and go to your nBrain app
2. **Open Developer Tools** (F12 or right-click → Inspect)
3. **Go to the Console tab**
4. **Type this command**:
   ```javascript
   localStorage.getItem('token')
   ```
5. **Press Enter**
6. **Copy the token** (it will be a long string without the quotes)

## Alternative Method:

1. **Go to Application/Storage tab** in Developer Tools
2. **Find Local Storage** in the sidebar
3. **Click on your domain**
4. **Find the `token` key**
5. **Copy its value**

## Running the Test Script:

```bash
python test_calendar_sync.py
```

Then paste:
1. Your auth token when prompted
2. The client ID (you can find this in the URL when viewing a client, e.g., `/client/638ebe98-369f-4547-ad34-21eb9a8bae03`) 