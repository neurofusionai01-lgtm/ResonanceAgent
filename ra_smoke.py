class Memory:
    def __init__(self): self.store=[]
    def add(self,k,v): self.store.append((k,v))
    def recall(self,k):
        for kk,vv in reversed(self.store):
            if kk==k: return vv

class IntentDetector:
    def detect(self, text):
        t=text.lower()
        if 'plan' in t: return 'PLANNING'
        if 'error' in t: return 'DEBUG'
        if 'schedule' in t or 'time' in t: return 'SCHEDULING'
        return 'GENERAL'

mem = Memory()
mem.add('session:last_topic', 'VR education flow')
mem.add('user:goal', 'build a lesson plan in VR')

idet = IntentDetector()
print('intent_of(\"we need a plan\") =', idet.detect('we need a plan'))
print('intent_of(\"there is an error in step 2\") =', idet.detect('there is an error in step 2'))
print('recall last_topic =', mem.recall('session:last_topic'))
print('recall user_goal =', mem.recall('user:goal'))
print('STATUS: resonance-agent core mock OK')