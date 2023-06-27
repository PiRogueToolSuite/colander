let locale_date_formatter = new Intl.DateTimeFormat({
    timeStyle: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: "numeric",
    minute: "numeric",
});
export const date_str = (d) => {
  if (!(d instanceof Date)) {
      d = new Date(d);
  }
  return locale_date_formatter.format(d);
};
