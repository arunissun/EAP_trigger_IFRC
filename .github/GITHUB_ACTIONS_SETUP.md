# GitHub Actions Setup for GloFAS Pipeline

## Required GitHub Secrets

To run this pipeline on GitHub Actions, you need to configure the following secrets in your repository:

### Step-by-Step: How to Add Secrets on GitHub

#### Step 1: Go to Your Repository Settings
1. Open your GitHub repository in a web browser
2. Click on the **Settings** tab (top navigation bar, far right)
   - ⚠️ Note: You need **admin** or **write** access to see this tab

#### Step 2: Navigate to Secrets Section
1. In the left sidebar, scroll down to find **Secrets and variables**
2. Click on **Secrets and variables** to expand it
3. Click on **Actions** (under Secrets and variables)

#### Step 3: Add New Secret
1. Click the green **New repository secret** button (top right)
2. You'll see a form with two fields:
   - **Name**: The secret name (must match exactly what the workflow expects)
   - **Secret**: The actual value (will be hidden after saving)

#### Step 4: Add Both Required Secrets
You need to add TWO secrets following the instructions below:

### Required Secrets

---

#### SECRET #1: `CDSAPI_URL`

**In the "Add Secret" form:**

- **Name field**: Enter exactly `CDSAPI_URL` (case-sensitive, no spaces)
- **Secret field**: Enter `https://cds.climate.copernicus.eu/api/v2`

Then click **Add secret** button.

---

#### SECRET #2: `CDSAPI_KEY`

**First, get your API key from Copernicus:**

1. Go to <https://cds.climate.copernicus.eu>
2. Click **Login** (top right) or **Register** if you don't have an account
3. After logging in, click on your **username** (top right)
4. Select **Your profile** from dropdown
5. Scroll down to find the **API key** section
6. Copy the entire API key (it looks like: `12345:abcdef12-3456-7890-abcd-ef1234567890`)

**Then, in GitHub "Add Secret" form:**

- **Name field**: Enter exactly `CDSAPI_KEY` (case-sensitive, no spaces)
- **Secret field**: Paste your full API key from Copernicus

Then click **Add secret** button.

---

### Verification

After adding both secrets:

1. Go back to **Settings** → **Secrets and variables** → **Actions**
2. You should see both secrets listed:
   - `CDSAPI_URL`
   - `CDSAPI_KEY`
3. You won't be able to see the values (GitHub hides them for security)
4. If you need to update them, click the secret name and choose "Update"

---

## Workflow Details

The workflow (`glofas_daily.yml`) runs:
- **Automatically**: Daily at 06:00 UTC
- **Manually**: Via the "Actions" tab → "Run workflow" button

### Steps performed:
1. Checkout repository
2. Set up Python 3.9 environment
3. Install system dependencies (libeccodes for GRIB reading)
4. Install Python packages from `requirements.txt`
5. Configure CDS API credentials
6. Download GloFAS data for configured countries
7. Merge GRIB files to NetCDF format
8. Generate hydrograph plots
9. Commit and push changes back to repository

## Important Notes

- ⚠️ The workflow commits generated data back to the repository
- 📊 Large data files may exceed GitHub's file size limits (consider Git LFS or external storage)
- 🔒 Never commit your CDS API credentials to the repository
- ⏱️ Download times may vary based on data volume and API response

## Testing the Workflow

1. Push the workflow file to GitHub
2. Go to the **Actions** tab in your repository
3. Click on **GloFAS Daily Pipeline**
4. Click **Run workflow** to test manually

## Troubleshooting

If the workflow fails:
- Check that secrets are properly configured
- Verify your CDS API key is valid
- Check the Actions logs for specific error messages
- Ensure return period files exist for all configured countries
