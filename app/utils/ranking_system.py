def calculate_rank(engagement_data, claps=0, claimed=False):
    """
    Calculate the ranking score for a pitch.
    
    The formula applied is:
    
        Rank Score = ((R * 4) + (RT * 2.5) + (L * 1.5) + (V / 800) + (C * 3)) * Boost
    
    Where:
      - R = replies (weight: 4)
      - RT = retweets (weight: 2.5)
      - L = likes (weight: 1.5)
      - V = views (normalized by dividing by 800)
      - C = claps (weight: 3)
      - Boost = 1.5 if the pitch is claimed, otherwise 1.0
      
    Parameters:
        engagement_data (dict): A dictionary containing engagement metrics with keys 'replies', 'retweets', 'likes', 'views'.
        claps (int): The number of claps received (default is 0).
        claimed (bool): True if the pitch is claimed by a verified founder, False otherwise.
        
    Returns:
        int: The final ranking score (rounded to the nearest integer).
    """
    replies = engagement_data.get('replies', 0)
    retweets = engagement_data.get('retweets', 0)
    likes = engagement_data.get('likes', 0)
    views = engagement_data.get('views', 0)
    
    # Calculate base score using weighted metrics.
    base_score = (replies * 4) + (retweets * 2.5) + (likes * 1.5) + (views / 800) + (claps * 3)
    
    # Claimed pitches get a 50% boost.
    boost_factor = 1.5 if claimed else 1.0
    final_score = base_score * boost_factor

    return round(final_score)
