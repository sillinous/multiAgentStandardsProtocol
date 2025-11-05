"""
Storytelling Agent
Frames technical work as compelling narratives for content creation and marketing
"""

import json
from datetime import datetime
from typing import Dict, List


class StorytellingAgent:
    """
    Transforms technical achievements into engaging stories
    for blog posts, social media, pitch decks, and marketing
    """

    def __init__(self):
        self.name = "StorytellingAgent"
        self.story_archive = []

    def capture_milestone(self, event: Dict) -> Dict:
        """
        Capture a technical milestone and transform it into a story beat

        Args:
            event: {
                'type': 'breakthrough'|'challenge'|'pivot'|'validation'|'partnership',
                'title': str,
                'technical_details': Dict,
                'timestamp': datetime,
                'impact': str
            }

        Returns:
            Story beat with narrative framing
        """
        story_beat = {
            'id': f"story_{len(self.story_archive) + 1}",
            'timestamp': event.get('timestamp', datetime.now()).isoformat(),
            'event_type': event['type'],
            'raw_event': event,
            'narrative': self._frame_as_narrative(event),
            'content_ideas': self._generate_content_ideas(event),
            'emotional_arc': self._identify_emotional_arc(event),
            'audience_value': self._extract_audience_value(event)
        }

        self.story_archive.append(story_beat)
        return story_beat

    def _frame_as_narrative(self, event: Dict) -> Dict:
        """Transform technical event into narrative structure"""

        templates = {
            'breakthrough': {
                'hook': f"What if {event.get('problem', 'the impossible')} became possible?",
                'challenge': f"The challenge: {event.get('technical_details', {}).get('obstacle', 'Complex technical problem')}",
                'solution': f"The breakthrough: {event.get('title', 'Innovation')}",
                'result': f"The impact: {event.get('impact', 'Significant progress')}"
            },
            'challenge': {
                'hook': f"Every builder faces this moment...",
                'setup': f"We hit a wall: {event.get('title', 'Major obstacle')}",
                'struggle': f"The reality: {event.get('technical_details', {}).get('problem', 'Complex issue')}",
                'lesson': f"What we learned: {event.get('impact', 'Valuable insight')}"
            },
            'pivot': {
                'hook': f"Sometimes the best path isn't the one you started on",
                'original_plan': f"We were building: {event.get('technical_details', {}).get('original', 'Initial approach')}",
                'insight': f"We realized: {event.get('title', 'New direction')}",
                'new_direction': f"Now we're: {event.get('impact', 'Pursuing better approach')}"
            },
            'validation': {
                'hook': f"The moment of truth...",
                'test': f"We validated: {event.get('title', 'Our hypothesis')}",
                'results': f"The data: {event.get('technical_details', {}).get('metrics', 'Positive results')}",
                'meaning': f"This proves: {event.get('impact', 'Concept works')}"
            },
            'partnership': {
                'hook': f"Opportunities come when you build in public",
                'context': f"The opportunity: {event.get('title', 'Collaboration')}",
                'value': f"Why it matters: {event.get('impact', 'Strategic advantage')}",
                'vision': f"Where it leads: {event.get('technical_details', {}).get('potential', 'Exciting future')}"
            }
        }

        return templates.get(event['type'], templates['breakthrough'])

    def _generate_content_ideas(self, event: Dict) -> List[Dict]:
        """Generate specific content pieces from this story beat"""

        ideas = []

        # Tweet thread
        ideas.append({
            'format': 'twitter_thread',
            'title': f"🧵 {event.get('title', 'Story')}",
            'estimated_tweets': 8,
            'angle': 'Technical journey with lessons',
            'cta': 'Follow for more real-time building'
        })

        # Blog post
        ideas.append({
            'format': 'blog_post',
            'title': event.get('title', 'Story'),
            'estimated_words': 1500,
            'angle': 'Deep technical breakdown with narrative',
            'cta': 'Try it yourself / Join the community'
        })

        # LinkedIn post
        ideas.append({
            'format': 'linkedin_post',
            'title': f"Lessons from {event.get('title', 'building')}",
            'estimated_words': 300,
            'angle': 'Professional insights and lessons',
            'cta': 'Connect to discuss'
        })

        # Short video script
        ideas.append({
            'format': 'video_script',
            'title': event.get('title', 'Story'),
            'estimated_duration': '3-5 minutes',
            'angle': 'Show the actual work + explain the why',
            'cta': 'Subscribe for more'
        })

        return ideas

    def _identify_emotional_arc(self, event: Dict) -> str:
        """Identify the emotional journey for storytelling"""

        arcs = {
            'breakthrough': 'struggle → insight → triumph',
            'challenge': 'confidence → setback → determination',
            'pivot': 'commitment → doubt → clarity',
            'validation': 'uncertainty → testing → proof',
            'partnership': 'solo journey → opportunity → collaboration'
        }

        return arcs.get(event['type'], 'journey → learning → growth')

    def _extract_audience_value(self, event: Dict) -> Dict:
        """What does the audience gain from this story?"""

        return {
            'for_builders': 'Technical approach they can apply',
            'for_learners': 'Concepts explained clearly',
            'for_investors': 'Proof of execution and progress',
            'for_partners': 'Evidence of capability',
            'for_customers': 'Transparency and trust'
        }

    def generate_twitter_thread(self, story_beat: Dict) -> List[str]:
        """Generate a Twitter thread from a story beat"""

        narrative = story_beat['narrative']
        event = story_beat['raw_event']

        thread = []

        # Tweet 1: Hook
        thread.append(narrative.get('hook', f"Building in public: {event.get('title', 'New update')}"))

        # Tweet 2: Setup/Challenge
        thread.append(narrative.get('challenge', narrative.get('setup', 'The challenge we faced...')))

        # Tweet 3-5: Technical details (broken down)
        tech_details = event.get('technical_details', {})
        if tech_details:
            for key, value in list(tech_details.items())[:3]:
                thread.append(f"{key}: {value}")

        # Tweet 6: Result/Solution
        thread.append(narrative.get('solution', narrative.get('result', event.get('impact', 'The outcome'))))

        # Tweet 7: Lesson/Insight
        thread.append(f"Key insight: {event.get('impact', 'Always learning')}")

        # Tweet 8: CTA
        thread.append("Following along? Drop a comment or DM - always happy to discuss!\n\nBuilding @Graytonomous - autonomous agents that improve themselves.")

        return thread

    def generate_blog_post_outline(self, story_beat: Dict) -> Dict:
        """Generate a blog post outline from a story beat"""

        event = story_beat['raw_event']
        narrative = story_beat['narrative']

        return {
            'title': event.get('title', 'Building in Public'),
            'subtitle': narrative.get('hook', ''),
            'sections': [
                {
                    'heading': 'The Challenge',
                    'content_points': [
                        narrative.get('challenge', narrative.get('setup', '')),
                        'Context and background',
                        'Why this matters'
                    ]
                },
                {
                    'heading': 'The Approach',
                    'content_points': [
                        'Technical architecture',
                        'Key decisions',
                        'Trade-offs considered'
                    ]
                },
                {
                    'heading': 'The Results',
                    'content_points': [
                        narrative.get('solution', narrative.get('result', '')),
                        'Metrics and validation',
                        'What worked / what didn\'t'
                    ]
                },
                {
                    'heading': 'Lessons Learned',
                    'content_points': [
                        event.get('impact', 'Key takeaways'),
                        'What I\'d do differently',
                        'Advice for others'
                    ]
                },
                {
                    'heading': 'What\'s Next',
                    'content_points': [
                        'Next steps',
                        'Open questions',
                        'How you can help/participate'
                    ]
                }
            ],
            'cta': 'Try it yourself | Follow the journey | Join the community'
        }

    def export_story_archive(self, filepath: str):
        """Export all stories for reference"""
        with open(filepath, 'w') as f:
            json.dump(self.story_archive, f, indent=2, default=str)

    def get_story_timeline(self) -> List[Dict]:
        """Get chronological story timeline"""
        return sorted(self.story_archive, key=lambda x: x['timestamp'])


# Example usage
if __name__ == "__main__":
    agent = StorytellingAgent()

    # Example: Capture Gerd partnership opportunity
    partnership_event = {
        'type': 'partnership',
        'title': 'German Mobility Startup Partnership Opportunity',
        'technical_details': {
            'challenge': 'Real-time multi-car hopping optimization',
            'solution': 'Multi-agent autonomous routing system',
            'validation': '3-hop solution in 72 minutes, $23 cost',
            'potential': 'Climate impact + European market entry + investor exposure'
        },
        'timestamp': datetime.now(),
        'impact': 'First major validation + potential $35k revenue + investor network access'
    }

    story = agent.capture_milestone(partnership_event)

    print("STORY NARRATIVE:")
    print(json.dumps(story['narrative'], indent=2))

    print("\n\nTWITTER THREAD:")
    thread = agent.generate_twitter_thread(story)
    for i, tweet in enumerate(thread, 1):
        print(f"\n{i}/ {tweet}")

    print("\n\nBLOG POST OUTLINE:")
    outline = agent.generate_blog_post_outline(story)
    print(json.dumps(outline, indent=2))
