import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function SearchBar({ 
  value, 
  onChange, 
  placeholder = "Pesquisar...",
  className = ""
}) {
  return (
    <div className={`relative ${className}`}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
      <Input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="pl-10 pr-10 h-10 bg-white border-gray-200 focus:border-[#E31A1A] focus:ring-[#E31A1A]"
        data-testid="search-input"
      />
      {value && (
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0 hover:bg-gray-100"
          onClick={() => onChange("")}
        >
          <X size={16} className="text-gray-400" />
        </Button>
      )}
    </div>
  );
}
