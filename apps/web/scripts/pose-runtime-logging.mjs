// The pinned native runtime writes this successful initialization notice to stderr.
// Adapt only our copied runtime, not the application's console or other SDK diagnostics.
export function configurePoseRuntimeLogging(source) {
  const original = "var err = console.error.bind(console);";
  if (source.split(original).length !== 2) {
    throw new Error("MediaPipe runtime logging changed. Review the adapter before upgrading.");
  }
  return source.replace(original, `var err = (...args) => {
  if (args.length === 1 && args[0] === "INFO: Created TensorFlow Lite XNNPACK delegate for CPU.") {
    console.info(...args);
  } else {
    console.error(...args);
  }
};`);
}
