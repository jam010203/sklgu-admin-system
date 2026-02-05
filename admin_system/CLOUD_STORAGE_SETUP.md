# Cloud Storage Setup for Production

## Problem
Fly.io uses **ephemeral storage** - uploaded files (profile pictures, logos, announcements) are deleted when the app restarts or redeploys.

## Current Temporary Fix
The app now serves a placeholder image when files are not found, preventing errors.

## Permanent Solution: Use Cloudinary

### Step 1: Create Cloudinary Account
1. Go to https://cloudinary.com/users/register/free
2. Sign up for free account (generous free tier)
3. Get your credentials from Dashboard:
   - Cloud name
   - API Key
   - API Secret

### Step 2: Add Environment Variables to Fly.io
In Fly.io Dashboard → Your App → Secrets:
```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### Step 3: Install Cloudinary Package
Add to `requirements.txt`:
```
cloudinary==1.36.0
```

### Step 4: Code Implementation
The app is already configured to use Cloudinary when environment variables are set. File uploads will automatically use Cloudinary instead of local storage.

## Alternative: AWS S3
If you prefer AWS S3:

1. Create S3 bucket
2. Add environment variables:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1
```

3. Add to requirements.txt:
```
boto3==1.28.0
```

## Verification
After setup:
1. Upload a profile picture or logo
2. Redeploy the app
3. Image should still be visible (stored in cloud, not local filesystem)

## Cost
- **Cloudinary Free Tier**: 25GB storage, 25GB bandwidth/month
- **AWS S3**: Pay-as-you-go (~$0.023/GB/month)

## Recommended
**Cloudinary** is recommended for this application due to:
- Free tier is generous
- Easy integration
- Built-in image optimization
- CDN included
