function NeoButton({ children, className = "", onClick, ...props }) {
  return (
    <button
      onClick={onClick}
      className={`neo-button text-light-gray hover:text-white transition-all duration-200 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export default NeoButton;
