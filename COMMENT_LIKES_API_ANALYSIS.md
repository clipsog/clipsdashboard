# Comment Likes API Analysis

## The Problem

The service name says **"TikTok Comments Likes | By Username"**, but we need to understand:
1. **What parameters does the API actually need?**
2. **How does it identify which comment to like?**
3. **Does it need a username, comment ID, or something else?**

## Test Results

All API tests returned **"Incorrect request"** - this could mean:
- ❌ Account has $0 balance (can't test real orders)
- ❌ Wrong parameter names
- ❌ Missing required parameters
- ❌ Different API structure than expected

## What We Know

### Service Details
- **Service ID**: 14718
- **Name**: "TikTok Comments Likes | By Username"
- **Minimum**: 50 likes
- **Rate**: $0.21 per 1,000

### User's Observation
You mentioned: *"comments likes the ID is 14718 but it says comments likes by username. then a place to put the link of the post but not the username?"*

This suggests:
- ✅ Website has a field for **post link** (video URL)
- ❓ Website might **not** have a username field (or it's hidden/optional)
- ❓ API might work differently than website

## Possible Scenarios

### Scenario 1: Video URL Only
The API might:
- Take only the video URL
- Automatically like comments on that video
- Pick comments randomly or by some algorithm

**API Call:**
```python
{
    'service': '14718',
    'link': 'https://www.tiktok.com/@user/video/123',
    'quantity': 50
}
```

### Scenario 2: Username Required
The API might need:
- Video URL
- Username of the commenter

**API Call:**
```python
{
    'service': '14718',
    'link': 'https://www.tiktok.com/@user/video/123',
    'quantity': 50,
    'username': 'commenter_username'  # or 'usernames', 'target', etc.
}
```

### Scenario 3: Comment ID Required
The API might need:
- Video URL
- Specific comment ID

**API Call:**
```python
{
    'service': '14718',
    'link': 'https://www.tiktok.com/@user/video/123',
    'quantity': 50,
    'comment_id': '1234567890'  # or 'cid', 'comment', etc.
}
```

## What We Need to Find Out

### Option 1: Check Website Form
1. Go to smmfollows.com
2. Navigate to service 14718
3. Check what fields the order form shows
4. See if there's a username/comment field

### Option 2: Check API Documentation
1. Look for smmfollows.com API docs
2. Check if they have examples for comment likes
3. See what parameters are documented

### Option 3: Test with Balance
1. Add small balance ($1-2)
2. Test different parameter combinations
3. See which one actually creates an order

### Option 4: Contact Support
1. Ask smmfollows.com support
2. Ask what parameters comment likes service needs
3. Get official API documentation

## Current Implementation

The bot currently:
1. ✅ Prompts for username at milestone
2. ✅ Sends username in API call (tries multiple parameter names)
3. ✅ Falls back to video URL only if no username

**Parameters tried:**
- `username`
- `usernames`
- `comment_username`
- `target`

## Recommendation

**Until we know for sure, the bot should:**

1. **Prompt for username** (as it does now)
2. **Try multiple parameter combinations**:
   - With username (various parameter names)
   - Without username (video URL only)
3. **Show clear error messages** if it fails
4. **Allow manual retry** with different parameters

**Best approach:**
- Check the website form first
- If website shows username field → use that parameter name
- If website only shows video URL → API probably works with URL only
- Test with small balance to confirm

## Next Steps

1. **Check website**: Look at the order form for service 14718
2. **Test with balance**: Add $1 and test different parameters
3. **Update bot**: Once we know the correct parameters, update the code
4. **Document**: Add clear instructions for users


