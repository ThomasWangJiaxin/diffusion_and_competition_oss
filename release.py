import requests
import csv
from typing import List, Dict, Optional
import os
from datetime import datetime
import time

class GitHubReleaseScraper:
    """
    A flexible scraper for GitHub repository releases using GitHub REST API
    """
    BASE_URL = "https://api.github.com/repos"
    
    def __init__(self, owner: str, repo: str, token: Optional[str] = None):
        """
        Initialize the scraper with repository details and optional GitHub token
        
        :param owner: GitHub repository owner/organization
        :param repo: Repository name
        :param token: Optional GitHub Personal Access Token for increased rate limits
        """
        self.owner = owner
        self.repo = repo
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"  # 指定 API 版本以确保兼容性
        }
        
        # Add authorization header if token is provided
        if token:
            self.headers["Authorization"] = f"token {token}"  # 修改为 "token" 而不是 "Bearer"
        
        # Directory to store output
        self.output_dir = "github_releases"
        os.makedirs(self.output_dir, exist_ok=True)

    def get_releases(self) -> List[Dict]:
        """
        Fetch all releases for the repository
        
        :return: List of release dictionaries
        """
        all_releases = []
        page = 1
        
        while True:
            url = f"{self.BASE_URL}/{self.owner}/{self.repo}/releases?page={page}&per_page=100"
            
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                releases = response.json()
                
                # 检查 API 返回数据是否为列表
                if not isinstance(releases, list):
                    print(f"Unexpected API response: {releases}")
                    break
                
                if not releases:
                    break
                
                print(f"Page {page} releases: {len(releases)}")
                for release in releases:
                    print(f"Release {release.get('tag_name')}: Assets = {release.get('assets', [])}")
                    if release.get('assets'):
                        for asset in release['assets']:
                            print(f"  - Asset {asset.get('name')}: Download Count = {asset.get('download_count', 0)}")
                
                all_releases.extend(releases)
                page += 1
                
                # Respect GitHub API rate limits
                if "X-RateLimit-Remaining" in response.headers:
                    remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                    if remaining < 10:
                        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                        wait_time = max(reset_time - int(time.time()), 0) + 1  # 加 1 秒以确保安全
                        print(f"Rate limit near exhaustion. Waiting {wait_time} seconds.")
                        time.sleep(wait_time)
            
            except requests.RequestException as e:
                print(f"Error fetching releases: {e}")
                break
        
        return all_releases

    def get_release_assets(self, release_id: int) -> List[Dict]:
        """
        Fetch assets for a specific release using the dedicated endpoint
        
        :param release_id: ID of the release
        :return: List of asset dictionaries
        """
        url = f"{self.BASE_URL}/{self.owner}/{self.repo}/releases/{release_id}/assets"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            assets = response.json()
            if not isinstance(assets, list):
                print(f"Unexpected assets response for release {release_id}: {assets}")
                return []
            return assets
        except requests.RequestException as e:
            print(f"Error fetching assets for release {release_id}: {e}")
            return []

    def compute_download_stats(self, release: Dict) -> Dict:
        """
        Compute download statistics for a specific release
        
        :param release: Release dictionary from GitHub API
        :return: Dictionary with download statistics
        """
        total_downloads = 0
        asset_details = []
        
        # 首先尝试从 release['assets'] 获取数据
        assets = release.get('assets', [])
        
        # 如果 assets 为空，尝试使用专用端点获取
        if not assets:
            release_id = release.get('id')
            if release_id:
                print(f"Assets empty for release {release.get('tag_name')}, fetching via dedicated endpoint...")
                assets = self.get_release_assets(release_id)
        
        # 计算下载量
        if assets:
            for asset in assets:
                asset_downloads = asset.get('download_count', 0)
                total_downloads += asset_downloads
                asset_details.append({
                    'name': asset.get('name', 'Unknown'),
                    'downloads': asset_downloads,
                    'size': asset.get('size', 0),
                    'content_type': asset.get('content_type', 'Unknown'),
                    'browser_download_url': asset.get('browser_download_url', '')
                })
        
        return {
            'total_downloads': total_downloads,
            'asset_details': asset_details
        }

    def extract_release_info(self, release: Dict) -> Dict:
        """
        Extract comprehensive information from a release
        
        :param release: Release dictionary from GitHub API
        :return: Processed release information
        """
        downloads = self.compute_download_stats(release)
        
        return {
            'tag_name': release.get('tag_name', 'N/A'),
            'name': release.get('name', 'N/A'),
            'published_at': release.get('published_at', 'N/A'),
            'created_at': release.get('created_at', 'N/A'),
            'total_downloads': downloads['total_downloads'],
            'prerelease': release.get('prerelease', False),
            'draft': release.get('draft', False),
            'body': (release.get('body', '')[:500] + '...') if release.get('body') else '',
            'asset_details': downloads['asset_details']
        }

    def save_to_csv(self, releases: List[Dict]):
        """
        Save releases information to a CSV file
        
        :param releases: List of processed release dictionaries
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"{self.repo}_releases_{timestamp}.csv")
        
        # Flatten asset details for CSV
        csv_data = []
        for release in releases:
            base_row = {k: v for k, v in release.items() if k != 'asset_details'}
            
            if release['asset_details']:
                for asset in release['asset_details']:
                    row = base_row.copy()
                    row.update({f'asset_{k}': v for k, v in asset.items()})
                    csv_data.append(row)
            else:
                csv_data.append(base_row)
        
        # Write to CSV
        if csv_data:
            keys = csv_data[0].keys()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                dict_writer = csv.DictWriter(f, keys)
                dict_writer.writeheader()
                dict_writer.writerows(csv_data)
            
            print(f"Releases saved to {filename}")

    def run(self):
        """
        Main method to fetch, process, and save releases
        """
        print(f"Fetching releases for {self.owner}/{self.repo}")
        releases = self.get_releases()
        
        # Debug: print number of releases found
        print(f"Found {len(releases)} releases")
        
        processed_releases = [self.extract_release_info(release) for release in releases]
        self.save_to_csv(processed_releases)
        
        return processed_releases

def main():
    # GitHub Personal Access Token (required)
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    # Example usage
    scraper = GitHubReleaseScraper(
        owner='bitcoin', 
        repo='bitcoin', 
        token=GITHUB_TOKEN
    )
    releases = scraper.run()
    
    # Print out download information for verification
    for release in releases:
        print(f"Release {release['tag_name']}: {release['total_downloads']} total downloads")
        for asset in release.get('asset_details', []):
            print(f"  - {asset.get('name', 'Unknown')}: {asset.get('downloads', 0)} downloads")

if __name__ == "__main__":
    main()