# Setting up Redis for nBrain Performance Optimization

## Why Redis?
- **In-memory caching**: Dramatically reduces database load
- **Sub-millisecond response times**: Much faster than database queries
- **Distributed caching**: Works across multiple server instances

## Setup Instructions for Render

### Option 1: Redis on Render (Recommended)
1. Go to your Render dashboard
2. Click "New +" → "Redis"
3. Configure:
   - **Name**: `nbrain-redis`
   - **Region**: Same as your backend (Oregon)
   - **Plan**: Start with Starter ($7/month)
   - **Maxmemory Policy**: `allkeys-lru` (removes least recently used keys)

4. After creation, copy the Internal Redis URL

### Option 2: Redis Cloud (Alternative)
1. Sign up at https://redis.com/try-free/
2. Create a free database (30MB)
3. Get the connection details

### Environment Variables
Add to your Render backend service:
```
REDIS_HOST=your-redis-instance.render.com
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
# Or use the full URL:
REDIS_URL=redis://red-xxxxx:6379
```

### Option 3: Use Upstash (Serverless Redis)
1. Sign up at https://upstash.com/
2. Create a Redis database
3. Use their REST API or Redis protocol
4. Add the connection string to Render

## Performance Improvements
With Redis caching:
- Client list loading: 45s → <100ms (after first load)
- AI queries: Cached for 5 minutes
- Communication lists: Cached for 30 seconds

## Cost Considerations
- **Render Redis Starter**: $7/month (1GB memory)
- **Redis Cloud Free**: 30MB free
- **Upstash Free**: 10,000 commands/day free

## Next Steps
1. Choose a Redis provider
2. Add environment variables
3. Deploy the updated code
4. Monitor cache hit rates 