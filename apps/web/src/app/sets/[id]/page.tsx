import { SavedSetReview } from "@/components/saved-set-review";

export default async function SavedSetPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <main id="main-content"><SavedSetReview id={id} /></main>;
}
