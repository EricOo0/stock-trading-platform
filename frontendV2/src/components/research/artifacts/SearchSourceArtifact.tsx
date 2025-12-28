import React from "react";

interface SearchResult {
  title: string;
  url?: string;
  href?: string;
  content?: string;
  body?: string;
  snippet?: string;
}

interface SearchSourceArtifactProps {
  data: SearchResult[] | { results: SearchResult[] };
  title?: string;
}

export const SearchSourceArtifact: React.FC<SearchSourceArtifactProps> = ({
  data,
  title,
}) => {
  const results =
    Array.isArray(data) ? data : (data as { results: SearchResult[] }).results || [];

  if (results.length === 0) {
    return (
      <div className="text-gray-500 p-3 text-sm italic">
        No search results available.
      </div>
    );
  }

  const getDomain = (url?: string) => {
    if (!url) return "Unknown Source";
    try {
      const domain = new URL(url).hostname;
      return domain.replace("www.", "");
    } catch {
      return url;
    }
  };

  return (
    <div className="w-full my-2">
      <h4 className="text-xs font-bold text-gray-500 mb-2 uppercase flex items-center gap-2 px-1">
        <svg
          className="w-3 h-3 text-blue-500"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M9 4.804A7.993 7.993 0 002 12a7.993 7.993 0 007 7.196V4.804z"></path>
          <path
            fillRule="evenodd"
            d="M11 4.804v14.392A7.993 7.993 0 0018 12a7.993 7.993 0 00-7-7.196z"
            clipRule="evenodd"
          ></path>
        </svg>
        {title || "Search References"}
      </h4>

      <div className="flex flex-col gap-2">
        {results.slice(0, 5).map((result, idx) => (
          <a
            key={idx}
            href={result.url || result.href}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex flex-col p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all duration-200"
          >
            <div className="flex items-center gap-2 mb-1">
              <div className="w-4 h-4 bg-gray-100 rounded flex items-center justify-center text-[10px] font-bold text-gray-400 group-hover:bg-blue-50 group-hover:text-blue-500">
                {idx + 1}
              </div>
              <h5 className="text-sm font-semibold text-gray-800 group-hover:text-blue-600 truncate flex-1">
                {result.title}
              </h5>
              <span className="text-[10px] text-gray-400 font-medium">
                {getDomain(result.url || result.href)}
              </span>
            </div>
            <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
              {result.content ||
                result.body ||
                result.snippet ||
                "No description available."}
            </p>
          </a>
        ))}
      </div>

      {results.length > 5 && (
        <div className="text-[10px] text-gray-400 mt-2 text-center italic">
          + {results.length - 5} more sources referenced
        </div>
      )}
    </div>
  );
};
