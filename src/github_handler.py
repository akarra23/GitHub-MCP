from github import Github
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class GitHubHandler:
    def __init__(self, token: str):
        self.github = Github(token)

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Process a query about GitHub and return relevant context.
        
        Args:
            query (str): The query about GitHub repositories/content
            context (Optional[Dict[str, Any]]): Additional context for the query
            
        Returns:
            List[Dict[str, Any]]: List of relevant GitHub context items
        """
        try:
            # Extract repository information from query or context
            repo_info = self._extract_repo_info(query, context)
            if not repo_info:
                return self._create_error_response("No repository information found in query")

            # Get repository
            repo = self.github.get_repo(repo_info)
            
            # Initialize response content
            content = []
            
            # Get repository information
            content.append({
                "type": "repository_info",
                "content": {
                    "name": repo.name,
                    "description": repo.description,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                    "url": repo.html_url
                },
                "metadata": {
                    "source": "github",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            })
            
            # Search repository contents based on query
            search_results = repo.get_contents("")
            relevant_files = self._filter_relevant_files(search_results, query)
            
            for file in relevant_files[:5]:  # Limit to 5 most relevant files
                content.append({
                    "type": "file_content",
                    "content": {
                        "name": file.name,
                        "path": file.path,
                        "url": file.html_url,
                        "content": file.decoded_content.decode('utf-8') if file.size < 100000 else "File too large"
                    },
                    "metadata": {
                        "source": "github",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                })
            
            return content
            
        except Exception as e:
            return self._create_error_response(str(e))
    
    def _extract_repo_info(self, query: str, context: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract repository information from query or context."""
        # First check context
        if context and "repository" in context:
            return context["repository"]
            
        # Try to find repository in format "owner/repo" in query
        import re
        repo_pattern = r'([a-zA-Z0-9-]+/[a-zA-Z0-9-_.]+)'
        match = re.search(repo_pattern, query)
        if match:
            return match.group(1)
            
        return None
    
    def _filter_relevant_files(self, files, query):
        """Filter files based on relevance to query."""
        # Simple relevance scoring based on filename and query terms
        query_terms = query.lower().split()
        scored_files = []
        
        for file in files:
            score = 0
            filename = file.name.lower()
            
            # Score based on filename matches
            for term in query_terms:
                if term in filename:
                    score += 1
                    
            # Prioritize certain file types
            if filename.endswith(('.md', '.txt', '.py', '.js', '.java')):
                score += 0.5
                
            if score > 0:
                scored_files.append((score, file))
                
        # Sort by score and return files
        return [file for score, file in sorted(scored_files, reverse=True)]
    
    def _create_error_response(self, error_message: str) -> List[Dict[str, Any]]:
        """Create an error response."""
        return [{
            "type": "error",
            "content": error_message,
            "metadata": {
                "source": "github",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }]
