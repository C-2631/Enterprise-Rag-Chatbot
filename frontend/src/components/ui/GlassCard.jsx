function GlassCard({ children, className = "", ...props }) {
  return (
    <div 
      className={`glass transition-all duration-300 ${className}`} 
      {...props}
    >
      {children}
    </div>
  );
}

export default GlassCard;
