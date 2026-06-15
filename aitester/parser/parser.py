import json
import urllib.request
from pathlib import Path
from urllib.error import URLError

import yaml
from aitester.core.exceptions import SpecLoadError
from aitester.parser.models import ParsedSpec
from aitester.parser.openapi import OpenAPIParser


def parse_spec(spec_path_or_url: str) -> ParsedSpec:
    """
    Loads an OpenAPI specification from a local file path or URL,
    parses it, and returns a ParsedSpec object.
    """
    spec_dict = None
    
    # Check if it's a URL
    if spec_path_or_url.startswith("http://") or spec_path_or_url.startswith("https://"):
        try:
            with urllib.request.urlopen(spec_path_or_url) as response:
                content = response.read().decode('utf-8')
                try:
                    spec_dict = json.loads(content)
                except json.JSONDecodeError:
                    try:
                        spec_dict = yaml.safe_load(content)
                    except yaml.YAMLError as e:
                        raise SpecLoadError(f"Failed to parse downloaded spec as JSON or YAML: {e}")
        except URLError as e:
            raise SpecLoadError(f"Failed to download spec from {spec_path_or_url}: {e}")
    else:
        # It's a file path
        path = Path(spec_path_or_url)
        if not path.is_file():
            raise SpecLoadError(f"File not found: {spec_path_or_url}")
            
        with open(path, "r", encoding="utf-8") as f:
            try:
                if path.suffix.lower() == ".json":
                    spec_dict = json.load(f)
                else:
                    spec_dict = yaml.safe_load(f)
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                raise SpecLoadError(f"Failed to parse spec file: {e}")
                
    if not isinstance(spec_dict, dict):
        raise SpecLoadError("Spec file did not parse into a JSON object.")
        
    parser = OpenAPIParser(spec_dict)
    return parser.parse()
